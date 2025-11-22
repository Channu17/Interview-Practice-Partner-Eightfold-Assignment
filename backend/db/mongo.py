from functools import lru_cache
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from config import settings

LOCAL_FALLBACK_URI = "mongodb://localhost:27017"


@lru_cache
def get_mongo_client() -> Optional[MongoClient]:
    uri = settings.mongo_uri or LOCAL_FALLBACK_URI
    try:
        return MongoClient(uri)
    except Exception:
        return None


def get_db() -> Optional[Database]:
    client = get_mongo_client()
    if not client or not settings.mongo_db_name:
        return None
    return client[settings.mongo_db_name]
