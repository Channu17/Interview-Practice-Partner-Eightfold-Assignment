from fastapi import APIRouter, HTTPException, status

from db import get_db
from models import UserRegistration

router = APIRouter()


@router.post("/register-user")
def register_user(payload: UserRegistration):
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    document = payload.model_dump()
    document["resume_url"] = None  # resume upload arrives later

    result = db["users"].insert_one(document)
    print(f"Inserted user {result.inserted_id}")
    return {"user_id": str(result.inserted_id)}


@router.post("/upload-resume")
def upload_resume():
    return {"message": "upload-resume placeholder"}
