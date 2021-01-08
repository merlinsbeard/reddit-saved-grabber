import os
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from logzero import logger
from dotenv import load_dotenv
from pydantic import BaseModel
from pymongo import DESCENDING, ASCENDING


from services.reddit import Reddit
from services.reddit_mongo import RedditMongo


load_dotenv()

reddit = Reddit(
    username=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET')
)

reddit_mongo = RedditMongo(
    os.getenv('MONGO_URL'),
    os.getenv('MONGO_DB'),
    os.getenv('MONGO_COLLECTION')
)

app: FastAPI = FastAPI()

origins: List[str] = [
    "http://localhost:8000",
    "https://r.benpaat.xyz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    """ Check if main service is up """
    return {"am" : "up"}

@app.get("/api_saved")
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

@app.get("/upload")
def upload_to_mongo(all: bool=False):
    """Saved data to mongoDB"""
    if all:
        data = reddit.get_all_list_parsed()
    else:
        reddit.get_list_saved()
        data = reddit.list_saved_parsed()
    reddit_mongo.insert(data)
    return("success")

class SavedObj(BaseModel):
    id: str
    author: str
    score: int
    over_18: bool
    permalink: str
    subreddit: str
    created: datetime
    date_added: datetime
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    media: Optional[dict] = None

class SavedResponseObj(BaseModel):
    total: int
    data: List[SavedObj]

@app.get('/saved', response_model=SavedResponseObj)
def list_saved_mongo(
    skip: int = Query(0),
    limit: int = Query(10),
    sort: Optional[List[str]] = Query(['_created',]),
    order: Optional[str] = Query("desc"),
    title: Optional[str] = Query(None),
    over_18: Optional[bool] = None,
    subreddit__in: Optional[List[str]] = Query(None),
    author__in: Optional[List[str]] = Query(None),
    post_hint__in: Optional[List[str]] = Query(None),
    domain__in: Optional[List[str]] = Query(None)
):
    """ Show data from mongo"""
    filter = {}
    filter.update({"$and": []})
    for f in [
        {'post_hint': post_hint__in},
        {'subreddit': subreddit__in},
        {'author': author__in},
        {'domain': domain__in},
        ]:

        x,y = list(f.items())[0]
        if y:
            field = {"$or": []}
            for n in y:
                field["$or"].append({x: n})
            filter["$and"].append(field)

    if not filter['$and']:
        del filter['$and']

    if over_18:
        filter.update({'over_18': over_18})
    if title:
        filter.update({'title': title})

    if order == 'desc':
        order = DESCENDING
    else:
        order = ASCENDING
    sort = [(s, order) for s in sort]

    data = reddit_mongo.list(
        filter=filter,
        skip=skip,
        limit=limit,
        sort=sort
    )
    resp: List[SavedObj] = []
    for n in data:
        # Convert _id to timestamp utc
        date_added = n.pop('_id').generation_time
        resp.append({
            **n,
            'date_added': date_added
        })

    return {
        "total": data.count(),
        "data": resp
    }

    
