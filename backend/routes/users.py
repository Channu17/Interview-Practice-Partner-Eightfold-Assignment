from fastapi import APIRouter

router = APIRouter()


@router.post("/register-user")
def register_user():
    return {"message": "register-user placeholder"}


@router.post("/upload-resume")
def upload_resume():
    return {"message": "upload-resume placeholder"}
