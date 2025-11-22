import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()


class Settings(BaseModel):
    mongo_uri: str = os.getenv("MONGO_URI", "")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "interview_practice")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv(
        "GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
    )
    groq_voice: str = os.getenv("GROQ_VOICE", "")
    gtts_language: str = os.getenv("GTTS_LANGUAGE", "en")
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def get_mongo_client() -> Optional[MongoClient]:
    if not settings.mongo_uri:
        return None
    return MongoClient(settings.mongo_uri)
