import os
from typing import Optional
from fastapi import FastAPI
from logzero import logger
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from services.reddit import Reddit

load_dotenv()

client = MongoClient(os.getenv('MONGO_URL'))
db = client[os.getenv('MONGO_DB')]
reddit = Reddit(
    username=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET')
)

app = FastAPI()

@app.get("/")
def read_root():
    """ Check if main service is up """
    return {"am" : "up"}

@app.get("/saved")
def collect_details(all: bool=False, after: Optional[str]=None, before: Optional[str] = None):
    """Return List of reddit saved based on account
    
    Default shows maximum of 25 items
    
    Query Params:
        all - bool - Shows all saved maximum of 1000 <- hard limit of reddit
        after - str - Cursor to show after page
        before - str - Cursor to show before page
    """
    if all:
        return reddit.get_all_list_parsed()
    if after:
        reddit.get_list_saved(params={"after": after})
    elif before:
        reddit.get_list_saved(params={"before": after})
    else:
        reddit.get_list_saved()
    return {
        "before": reddit.list_saved_before,
        "after": reddit.list_saved_after,
        "data": reddit.list_saved_parsed(),
    }

@app.get("/insert_data")
def upload_to_mongo(all: bool=False):
    """Saved data to mongoDB"""
    if all:
        data = reddit.get_all_list_parsed()
    else:
        reddit.get_list_saved()
        data = reddit.list_saved_parsed()
    saved_collection = db.saved
    try:
        saved_collection.insert_many(data, ordered=False)
    except BulkWriteError:
        logger.info('Skipping duplicate')
    return("success")