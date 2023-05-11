import json
import logging
import os
import time

from beem import Hive
from beem.block import Blocks
from beem.blockchain import Blockchain
from dotenv import load_dotenv
from pymongo import MongoClient

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

# Connect to MongoDB
mongo_db = os.getenv("MONGO_DB")
client = MongoClient(mongo_db)
db = client.torrents
settings_collection = db.settings
torrents_collection = db.torrents

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
    # Find the last block number in the settings collection
    last_block_data = settings_collection.find_one({"id": "info"}, {"last_block": 1})
    if last_block_data.get("last_block") is not None:
        return last_block_data["last_block"]
    # If the last block number is not found, use the GENISYS_BLOCK environment variable
    last_block = int(os.getenv("GENISYS_BLOCK"))
    set_block("last_block", last_block)
    # Update the settings collection with the new last block number
    settings_collection.update_one(
        {"id": "info"}, {"$set": {"genisys": last_block}}, upsert=True
    )
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
    # Update the settings collection with the new key-value pair
    settings_collection.update_one({"id": "info"}, {"$set": {key: value}}, upsert=True)


def process_custom_json_operation(block, operation):
    """
    Process a MagnetBank custom JSON operation.

    Args:
    ----
    block (beem.block.Block): The block containing the operation.
    operation (dict): The custom JSON operation.
    """
    time = block["timestamp"].isoformat()
    number = block.block_num
    submitted_by = operation["value"]["required_posting_auths"][0]
    json_data = json.loads(operation["value"]["json"])
    # Check if the data is well-formed
    if all(
        key in json_data for key in ["hash", "file_name", "category", "announce_url"]
    ):
        # Add additional data to the JSON object
        json_data.update(
            {
                "hash": json_data["hash"].upper(),
                "timestamp": time,
                "submitted_by": submitted_by,
                "block_number": number,
            }
        )
        # Check if the hash key already exists in the database
        if torrents_collection.find_one({"hash": json_data["hash"]}) is None:
            # If the hash key does not exist, add the JSON object to the database
            logger.info(
                f"Hash key {json_data['hash']} added to database - {json_data['file_name']} by {json_data['submitted_by']}"
            )
            torrents_collection.insert_one(json_data)
        else:
            # If the hash key already exists, log a warning
            logger.warning(
                f"Hash key {json_data['hash']} already exists in the database."
            )
    elif json_data.get("action") and submitted_by == ADMIN_ACCOUNT:
        if json_data.get("action") == "update":
            torrents_collection.update_one(
                {"hash": json_data["hash"]},
                {"$set": {"category": json_data["category"]}},
                upsert=True,
            )
            logger.info(
                f"Hash key {json_data['hash']} updated to {json_data['category']} by {submitted_by}"
            )
        if json_data.get("action") == "delete":
            torrents_collection.delete_one({"hash": json_data["hash"]})
            logger.info(f"Hash key {json_data['hash']} deleted by {submitted_by}")
    else:
        # If the data is not well-formed, log a warning
        logger.warning("Malformed data received.")


def process_blocks(start_block):
    """
    Process blocks starting from a given block number.

    Args:
    ----
    start_block (int): The block number to start processing from.
    """
    # Retrieve blocks from the Hive blockchain
    blocks = Blocks(start_block, 1000, blockchain_instance=hive)
    logger.debug(f"{len(blocks)} blocks retrieved")
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
        # Update the last block number in the settings collection
        set_block("last_block", last_block)


def process_blocks_in_batches(start_block, end_block):
    """
    Process blocks in batches of 1000.

    Args:
    ----
    start_block (int): The block number to start processing from.
    end_block (int): The block number to stop processing at.
    """
    rounds = (end_block - start_block) // 1000 + 1
    for r in range(rounds):
        logger.debug(
            f"Round {r+1}/{rounds} from block {start_block+1} to block {min(start_block+1000, end_block)}"
        )
        process_blocks(start_block)
        start_block = min(start_block + 1000, end_block)


def main():
    """
    Run the MagnetBank Node.
    """
    while True:
        try:
            # Get the current block number from the Hive blockchain
            head_block = Blockchain(blockchain_instance=hive).get_current_block_num()
            # Update the head block number in the settings collection
            set_block("head_block", head_block)
            # Get the last block number from the settings collection
            last_block = get_last_block()
            # Calculate the difference between the head block and the last block
            difference = head_block - last_block
            logger.info(
                f"Current block: {head_block} Last block: {last_block} Difference: {difference}"
            )
            # Process blocks in batches of 1000
            process_blocks_in_batches(last_block, head_block)
            # Wait for the specified amount of time before processing the next batch of blocks
            sleep_time = float(os.getenv("SLEEP_TIME"))
            time.sleep(sleep_time)
        except Exception as e:
            # Log any errors that occur
            logger.error(e)


if __name__ == "__main__":
    main()
