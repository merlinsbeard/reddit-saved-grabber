from typing import Optional
from logzero import logger
from pymongo import MongoClient
from pymongo.errors import BulkWriteError


class RedditMongo:
    
    def __init__(self, mongo_url, mongo_db, mongo_collection):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

        client = MongoClient(self.mongo_url)
        db = client[self.mongo_db]
        self.db_collection = db[self.mongo_collection]

    def insert(self, data: dict) -> None:
        try:
            self.db_collection.insert_many(data, ordered=False)
        except BulkWriteError:
            logger.info('Skipping Duplicate')

    def list(self,
             filter: Optional[dict],
             skip: int = 0,
             limit: int = 10,
             sort: Optional[list] = [('_id', -1)]) -> list:

        return self.db_collection.find(
            filter=filter,
            skip=skip,
            limit=limit
        ).sort(sort)
