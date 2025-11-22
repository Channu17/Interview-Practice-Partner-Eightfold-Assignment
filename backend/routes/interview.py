from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db import get_interviews_collection
from models import InterviewSession

router = APIRouter()


class StartInterviewRequest(BaseModel):
    user_id: str
    domain: str
    experience: str


class ProcessAnswerRequest(BaseModel):
    interview_id: str
    user_id: str
    answer: str


class EndInterviewRequest(BaseModel):
    interview_id: str
    user_id: str


@router.get("/get-domains")
def get_domains():
    return {
        "domains": [
            "Sales",
            "Python Developer",
            "Full Stack Developer",
            "Data Science",
        ]
    }


@router.post("/start-interview")
def start_interview(payload: StartInterviewRequest):
    collection = get_interviews_collection()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    session = InterviewSession(
        user_id=payload.user_id,
        domain=payload.domain,
        experience=payload.experience,
        questions=["Tell me about yourself."],
        answers=[],
    )
    result = collection.insert_one(session.model_dump())
    return {
        "interview_id": str(result.inserted_id),
        "question": "Tell me about yourself.",
    }


@router.post("/process-answer")
def process_answer(payload: ProcessAnswerRequest):
    collection = get_interviews_collection()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    try:
        interview_object_id = ObjectId(payload.interview_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid interview id")

    update_result = collection.update_one(
        {"_id": interview_object_id, "user_id": payload.user_id},
        {
            "$push": {"answers": payload.answer, "questions": "Why are you interested in this role?"},
        },
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"question": "Why are you interested in this role?"}


@router.post("/end-interview")
def end_interview(payload: EndInterviewRequest):
    collection = get_interviews_collection()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    try:
        interview_object_id = ObjectId(payload.interview_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid interview id")

    update_result = collection.update_one(
        {"_id": interview_object_id, "user_id": payload.user_id},
        {"$set": {"status": "completed"}},
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"feedback": "Thank you for completing the mock interview."}
