from pymongo import MongoClient

from config import settings


def get_mongo_client() -> MongoClient | None:
    if not settings.mongo_uri:
        return None
    return MongoClient(settings.mongo_uri)
