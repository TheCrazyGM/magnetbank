import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables

load_dotenv()

ADMIN = os.getenv("ADMIN_ACCOUNT")
HIVE_NODE = os.getenv("HIVE_NODE")
MONGO_URI = os.getenv("MONGO_DB")

client = MongoClient(MONGO_URI)
collection = client["torrents"]["torrents"]
settings = client["torrents"]["settings"]

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
)
logger = logging.getLogger("magnetbank")
logger.setLevel(logging.DEBUG)
