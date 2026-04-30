import json
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("MagnetBank Importer")

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import (  # noqa: E402
    Setting,
    Torrent,
    get_db_engine,
    get_session,
)


def import_settings(session, file_path):
    if not os.path.exists(file_path):
        logger.warning(f"Settings file not found: {file_path}")
        return

    logger.info(f"Importing settings from {file_path}...")
    with open(file_path, "r") as f:
        data = json.load(f)

    count = 0
    for doc in data:
        doc_id = doc.get("id")
        if not doc_id:
            continue

        for key, value in doc.items():
            if key in ["_id", "id"]:
                continue

            # Convert value to string for our simple Text storage
            str_value = (
                json.dumps(value) if isinstance(value, (list, dict)) else str(value)
            )

            setting = session.query(Setting).filter_by(id=doc_id, key=key).first()
            if setting:
                setting.value = str_value
            else:
                setting = Setting(id=doc_id, key=key, value=str_value)
                session.add(setting)
            count += 1

    session.commit()
    logger.info(f"Imported {count} setting keys.")


def import_torrents(session, file_path):
    if not os.path.exists(file_path):
        logger.warning(f"Torrents file not found: {file_path}")
        return

    logger.info(f"Importing torrents from {file_path}...")
    with open(file_path, "r") as f:
        data = json.load(f)

    count = 0
    skipped = 0
    for doc in data:
        info_hash = doc.get("hash")
        if not info_hash:
            skipped += 1
            continue

        info_hash = info_hash.upper()

        # Check if exists
        existing = session.query(Torrent).filter_by(hash=info_hash).first()
        if existing:
            skipped += 1
            continue

        # Handle announce_url which might be a list (as seen in error)
        announce_url = doc.get("announce_url")
        if isinstance(announce_url, list):
            # Pick first valid if list, else empty string
            announce_url = announce_url[0] if announce_url else ""

        new_torrent = Torrent(
            hash=info_hash,
            file_name=doc.get("file_name", "Unknown"),
            category=doc.get("category"),
            announce_url=str(announce_url) if announce_url else None,
            timestamp=doc.get("timestamp"),
            submitted_by=doc.get("submitted_by"),
            block_number=doc.get("block_number"),
        )
        session.add(new_torrent)
        count += 1

        # Batch commit every 500 records
        if count % 500 == 0:
            session.commit()
            logger.info(f"Progress: {count} torrents imported...")

    session.commit()
    logger.info(
        f"Finished. Imported {count} torrents, skipped {skipped} (already exist or invalid)."
    )


if __name__ == "__main__":
    db_path = os.getenv("SQLITE_DB", "magnetbank.db")
    engine = get_db_engine(db_path)
    session = get_session(engine)

    try:
        import_settings(session, "data/torrents.settings.json")
        import_torrents(session, "data/torrents.torrents.json")
        logger.info("Import completed successfully.")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        session.rollback()
    finally:
        session.close()
