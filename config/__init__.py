import datetime
import logging

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
collection = client["torrents"]["torrents"]
settings = client["torrents"]["settings"]

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
)
logger = logging.getLogger("magnetbank")
logger.setLevel(logging.DEBUG)


class MongoHandler(logging.Handler):
    """
    A custom logging handler that writes log records to a MongoDB collection.
    """

    def __init__(self, db_uri, db_name, collection_name):
        """
        Initialize the MongoHandler with the specified database URI, database name, and collection name.

        :param db_uri: The URI of the MongoDB instance.
        :param db_name: The name of the database to use.
        :param collection_name: The name of the collection to use.
        """
        logging.Handler.__init__(self)
        client = MongoClient(db_uri)
        self.collection = client[db_name][collection_name]

    def emit(self, record):
        """
        Write a log record to the MongoDB collection.

        :param record: The log record to write.
        """
        log_document = {
            "app_name": record.name,
            "log_level": record.levelname,
            "message": record.msg,
            "timestamp": datetime.datetime.fromtimestamp(record.created),
        }
        self.collection.insert_one(log_document)
