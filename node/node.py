import json
import logging
import os
import sys
import time
from typing import Dict

from dotenv import load_dotenv
from nectar import Hive
from nectar.block import Blocks
from nectar.blockchain import Blockchain
from sqlalchemy.orm import Session

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import Setting, Torrent, get_db_engine, get_session
from utils.helpers import is_safe_url, is_valid_info_hash, sanitize_input

# Load environment variables
load_dotenv()

# Configuration
ADMIN_ACCOUNT = os.getenv("ADMIN_ACCOUNT")
HIVE_NODES = os.getenv("HIVE_NODE", "https://api.hive.blog").split(",")
GENISYS_BLOCK = int(os.getenv("GENISYS_BLOCK", 0))
DB_PATH = os.getenv("SQLITE_DB", "magnetbank.db")

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MagnetBankNode")


class MagnetBankNode:
    def __init__(self):
        self.engine = get_db_engine(DB_PATH)
        self.hive = Hive(nodes=HIVE_NODES)
        self.blockchain = Blockchain(blockchain_instance=self.hive)

    def get_session(self) -> Session:
        return get_session(self.engine)

    def get_setting(self, session: Session, key: str, default=None) -> any:
        setting = session.query(Setting).filter_by(id="info", key=key).first()
        if setting:
            try:
                return int(setting.value)
            except (ValueError, TypeError):
                return setting.value
        return default

    def set_setting(self, session: Session, key: str, value: any):
        setting = session.query(Setting).filter_by(id="info", key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(id="info", key=key, value=str(value))
            session.add(setting)
        session.commit()

    def process_operation(
        self, session: Session, block_num: int, timestamp: str, op: Dict
    ):
        if op["type"] != "custom_json_operation" or op["value"]["id"] != "MagnetBank":
            return

        try:
            submitted_by = op["value"]["required_posting_auths"][0]
            json_data = json.loads(op["value"]["json"])
        except (IndexError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Malformed operation in block {block_num}: {e}")
            return

        # Handle New Torrent Entry
        if all(
            key in json_data
            for key in ["hash", "file_name", "category", "announce_url"]
        ):
            raw_hash = str(json_data["hash"]).upper().strip()
            raw_name = str(json_data["file_name"])
            raw_cat = str(json_data["category"]).upper().strip()
            raw_announce = str(json_data["announce_url"])
            raw_source = json_data.get("exact_source")

            # --- SECURITY & VALIDATION CHECKS ---

            # 1. Validate Info Hash Format
            if not is_valid_info_hash(raw_hash):
                logger.warning(
                    f"REJECTED: Invalid hash format '{raw_hash}' from @{submitted_by}"
                )
                return

            # 2. Sanitize and Limit Filename (XSS Protection + DB sanity)
            file_name = sanitize_input(raw_name, max_length=255)
            if not file_name:
                logger.warning(
                    f"REJECTED: Empty or malicious filename from @{submitted_by}"
                )
                return

            # 3. Validate and Sanitize Category
            allowed_cats = ["VIDEO", "AUDIO", "APP", "TEXT", "OTHER"]
            category = raw_cat if raw_cat in allowed_cats else "OTHER"

            # 4. Validate Announce URL Scheme
            if not is_safe_url(raw_announce):
                logger.warning(
                    f"REJECTED: Unsafe announce URL '{raw_announce}' from @{submitted_by}"
                )
                return

            # 5. Validate Exact Source (if present)
            exact_source = None
            if raw_source:
                if is_safe_url(raw_source, allowed_schemes=["http", "https"]):
                    exact_source = raw_source
                else:
                    logger.warning(
                        f"DROPPED: Unsafe source URL '{raw_source}' from @{submitted_by}"
                    )

            # --- DATA INTEGRITY ---

            existing = session.query(Torrent).filter_by(hash=raw_hash).first()
            if not existing:
                new_torrent = Torrent(
                    hash=raw_hash,
                    file_name=file_name,
                    category=category,
                    announce_url=raw_announce,
                    exact_source=exact_source,
                    timestamp=timestamp,
                    submitted_by=submitted_by,
                    block_number=block_num,
                )
                session.add(new_torrent)
                session.commit()
                logger.info(f"ADDED: {raw_hash} | {file_name} by @{submitted_by}")
            else:
                logger.debug(f"DUPLICATE: {raw_hash} already in database.")

        # Handle Admin Actions
        elif json_data.get("action") and submitted_by == ADMIN_ACCOUNT:
            action = json_data.get("action")
            info_hash = json_data.get("hash", "").upper()
            torrent = session.query(Torrent).filter_by(hash=info_hash).first()

            if torrent:
                if action == "update":
                    torrent.category = json_data.get(
                        "category", torrent.category
                    ).upper()
                    session.commit()
                    logger.info(
                        f"UPDATED: {info_hash} category set to {torrent.category}"
                    )
                elif action == "delete":
                    session.delete(torrent)
                    session.commit()
                    logger.info(f"DELETED: {info_hash}")

    def sync(self):
        logger.info("Initializing synchronization...")

        with self.get_session() as session:
            last_block = self.get_setting(session, "last_block")
            if last_block is None:
                last_block = GENISYS_BLOCK
                self.set_setting(session, "last_block", last_block)
                self.set_setting(session, "genisys", last_block)
                logger.info(f"Starting from GENISYS block: {last_block}")
            else:
                logger.info(f"Resuming from block: {last_block}")

        while True:
            try:
                current_head = self.blockchain.get_current_block_num()

                if current_head > last_block:
                    # Process blocks in chunks
                    batch_size = 100
                    stop_block = min(last_block + batch_size, current_head)

                    logger.info(
                        f"Scanning blocks: {last_block + 1} to {stop_block} (Head: {current_head})"
                    )

                    # hive-nectar signature: __init__(self, starting_block_num, count=1000, ...)
                    batch_count = stop_block - last_block
                    blocks = Blocks(
                        last_block + 1,
                        count=batch_count,
                        blockchain_instance=self.hive,
                    )

                    with self.get_session() as session:
                        for block in blocks:
                            ts = block["timestamp"].isoformat()
                            bn = block.block_num
                            for op in block.operations:
                                self.process_operation(session, bn, ts, op)
                            last_block = bn

                        # Update progress in DB
                        self.set_setting(session, "last_block", last_block)
                        self.set_setting(session, "head_block", current_head)

                else:
                    logger.debug("Chain head reached. Waiting for new blocks...")
                    time.sleep(3)

            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(10)
                # Re-initialize hive connection on error
                self.hive = Hive(nodes=HIVE_NODES)
                self.blockchain = Blockchain(blockchain_instance=self.hive)


if __name__ == "__main__":
    node = MagnetBankNode()
    try:
        node.sync()
    except KeyboardInterrupt:
        logger.info("Node shutdown requested by user.")
