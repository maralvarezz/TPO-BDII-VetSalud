from __future__ import annotations

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database


def get_mongo_database() -> Database:
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    mongo_db = os.getenv("MONGO_DB", "vetsalud")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return client[mongo_db]
