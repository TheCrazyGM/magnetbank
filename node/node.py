import json
import logging
import os
import time
import sys

from nectar import Hive
from nectar.block import Blocks
from nectar.blockchain import Blockchain
from dotenv import load_dotenv

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db_engine, get_session, Torrent, Setting

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
logger = logging.getLogger("MagnetBank Node")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Admin account for DMCA takedown and Changes to categories
ADMIN_ACCOUNT = os.getenv("ADMIN_ACCOUNT")

# Database setup
DB_PATH = os.getenv("SQLITE_DB", "magnetbank.db")
engine = get_db_engine(DB_PATH)
db_session = get_session(engine)

# Connect to Hive blockchain
hive_nodes = os.getenv("HIVE_NODE")
hive = Hive(nodes=hive_nodes)


def get_last_block():
    """
    Retrieve the last block number from the database.

    Returns
    -------
    int: The last block number.
    """
    last_block_data = (
        db_session.query(Setting).filter_by(id="info", key="last_block").first()
    )
    if last_block_data and last_block_data.value:
        return int(last_block_data.value)

    # If the last block number is not found, use the GENISYS_BLOCK environment variable
    last_block = int(os.getenv("GENISYS_BLOCK", 0))
    set_block("last_block", last_block)

    # Matching original logic for 'genisys' key
    set_block("genisys", last_block)

    logger.warning(f"Last block not found using root starting block {last_block}.")
    return last_block


def set_block(key, value):
    """
    Set a key-value pair in the settings collection.

    Args:
    ----
    key (str): The key to set.
    value (any): The value to set.
    """
    setting = db_session.query(Setting).filter_by(id="info", key=key).first()
    if setting:
        setting.value = str(value)
    else:
        setting = Setting(id="info", key=key, value=str(value))
        db_session.add(setting)
    db_session.commit()


def process_custom_json_operation(block, operation):
    """
    Process a MagnetBank custom JSON operation.

    Args:
    ----
    block (nectar.block.Block): The block containing the operation.
    operation (dict): The custom JSON operation.
    """
    timestamp = block["timestamp"].isoformat()
    number = block.block_num
    submitted_by = operation["value"]["required_posting_auths"][0]
    try:
        json_data = json.loads(operation["value"]["json"])
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received.")
        return

    # Check if the data is well-formed
    if all(
        key in json_data for key in ["hash", "file_name", "category", "announce_url"]
    ):
        info_hash = json_data["hash"].upper()

        # Check if the hash key already exists in the database
        existing = db_session.query(Torrent).filter_by(hash=info_hash).first()
        if not existing:
            new_torrent = Torrent(
                hash=info_hash,
                file_name=json_data["file_name"],
                category=json_data["category"],
                announce_url=json_data["announce_url"],
                timestamp=timestamp,
                submitted_by=submitted_by,
                block_number=number,
            )
            db_session.add(new_torrent)
            db_session.commit()
            logger.info(
                f"Hash key {info_hash} added to database - {json_data['file_name']} by {submitted_by}"
            )
        else:
            logger.warning(f"Hash key {info_hash} already exists in the database.")
    elif json_data.get("action") and submitted_by == ADMIN_ACCOUNT:
        info_hash = json_data.get("hash", "").upper()
        if json_data.get("action") == "update":
            torrent = db_session.query(Torrent).filter_by(hash=info_hash).first()
            if torrent:
                torrent.category = json_data["category"]
                db_session.commit()
                logger.info(
                    f"Hash key {info_hash} updated to {json_data['category']} by {submitted_by}"
                )
        elif json_data.get("action") == "delete":
            torrent = db_session.query(Torrent).filter_by(hash=info_hash).first()
            if torrent:
                db_session.delete(torrent)
                db_session.commit()
                logger.info(f"Hash key {info_hash} deleted by {submitted_by}")
    else:
        logger.warning("Malformed data received.")


def process_blocks(start_block):
    """
    Process blocks starting from a given block number.

    Args:
    ----
    start_block (int): The block number to start processing from.
    """
    blocks = Blocks(start_block, 1000, blockchain_instance=hive)
    # Process each block
    for block in blocks:
        last_block = block.block_num
        # Check if the block contains a MagnetBank custom JSON operation
        for operation in block.operations:
            if (
                operation["type"] == "custom_json_operation"
                and operation["value"]["id"] == "MagnetBank"
            ):
                process_custom_json_operation(block, operation)

        # Periodically update the last block number
        if last_block % 10 == 0:
            set_block("last_block", last_block)
            logger.info(f"Processed up to block {last_block}")

    set_block("last_block", last_block)


if __name__ == "__main__":
    while True:
        try:
            last_block = get_last_block()
            blockchain = Blockchain(blockchain_instance=hive)
            current_block = blockchain.get_current_block_num()

            if current_block > last_block:
                process_blocks(last_block + 1)
            else:
                logger.info("Waiting for new blocks...")
                time.sleep(3)
        except Exception as e:
            logger.error(f"Error processing blocks: {e}")
            time.sleep(10)
