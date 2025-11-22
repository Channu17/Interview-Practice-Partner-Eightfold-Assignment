from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from db import get_db
from models import UserRegistration

router = APIRouter()

RESUME_DIR = Path(__file__).resolve().parent.parent / "resumes"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

@router.post("/register-user")
def register_user(payload: UserRegistration):
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    document = payload.model_dump()
    document["resume_present"] = bool(document.get("resume_url"))

    result = db["users"].insert_one(document)
    print(f"Inserted user {result.inserted_id}")
    return {"user_id": str(result.inserted_id)}

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF or DOC/DOCX files are allowed",
        )

    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid4().hex}{suffix}"
    save_path = RESUME_DIR / unique_name

    contents = await file.read()
    with save_path.open("wb") as handle:
        handle.write(contents)

    resume_url = f"resumes/{unique_name}"
    return {"resume_url": resume_url, "filename": file.filename}
