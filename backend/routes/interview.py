from itertools import zip_longest
from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db import get_interviews_collection
from llm import evaluate_interview, generate_interview_question
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

    first_question = generate_interview_question([], payload.domain, payload.experience)
    session = InterviewSession(
        user_id=payload.user_id,
        domain=payload.domain,
        experience=payload.experience,
        questions=[first_question],
        answers=[],
    )
    result = collection.insert_one(session.model_dump())
    return {
        "interview_id": str(result.inserted_id),
        "question": first_question,
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

    session = collection.find_one({"_id": interview_object_id, "user_id": payload.user_id})
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")

    if session.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    history: List[dict[str, str]] = [
        {"question": q, "answer": a}
        for q, a in zip(session.get("questions", []), session.get("answers", []))
    ]
    last_question = session.get("questions", [])[-1] if session.get("questions") else "Tell me about yourself."
    history.append({"question": last_question, "answer": payload.answer})

    next_question = generate_interview_question(
        history,
        session.get("domain", ""),
        session.get("experience", ""),
    )

    update_ops = {
        "$push": {"answers": payload.answer},
    }
    if next_question:
        update_ops["$push"]["questions"] = next_question

    collection.update_one(
        {"_id": interview_object_id, "user_id": payload.user_id},
        update_ops,
    )
    return {"question": next_question}


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

    session = collection.find_one({"_id": interview_object_id, "user_id": payload.user_id})
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")

    history: List[dict[str, str]] = [
        {"question": question or "", "answer": answer or ""}
        for question, answer in zip_longest(
            session.get("questions", []),
            session.get("answers", []),
            fillvalue="",
        )
    ]

    feedback = evaluate_interview(
        history,
        session.get("domain", ""),
        session.get("experience", ""),
    )

    collection.update_one(
        {"_id": interview_object_id, "user_id": payload.user_id},
        {"$set": {"status": "completed", "feedback": feedback}},
    )
    return {"feedback": feedback}
