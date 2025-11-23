from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db import get_db, get_interviews_collection
from llm import evaluate_interview, generate_interview_question
from models import InterviewSession
from resume_parser import build_resume_context, extract_resume_text

router = APIRouter()
RESUME_DIR = Path(__file__).resolve().parent.parent / "resumes"


def _ensure_resume_context(user_doc: dict[str, Any], db) -> str:
    existing = (user_doc.get("resume_context") or "").strip()
    if existing:
        return existing
    resume_url = (user_doc.get("resume_url") or "").strip()
    if not resume_url:
        return ""
    resume_path = RESUME_DIR / Path(resume_url).name
    text = extract_resume_text(resume_path)
    context = build_resume_context(text)
    if context:
        db["users"].update_one({"_id": user_doc["_id"]}, {"$set": {"resume_context": context}})
    return context


class StartInterviewRequest(BaseModel):
    user_id: str
    domain: str
    experience: str


class ProcessAnswerRequest(BaseModel):
    interview_id: str
    user_id: str
    answer: str
    behavior_override: Optional[str] = None


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
    db = get_db()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not configured",
        )

    try:
        user_object_id = ObjectId(payload.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")

    user = db["users"].find_one({"_id": user_object_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    resume_context = _ensure_resume_context(user, db)

    first_question = generate_interview_question(
        [],
        payload.domain,
        payload.experience,
        resume_context=resume_context,
    )
    session = InterviewSession(
        user_id=payload.user_id,
        domain=payload.domain,
        experience=payload.experience,
        questions=[first_question["question"]],
        answers=[],
        behaviors=[],
        resume_context=resume_context,
    )
    result = collection.insert_one(session.model_dump())
    return {
        "interview_id": str(result.inserted_id),
        "question": first_question["question"],
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

    questions = session.get("questions", []) or []
    answers = session.get("answers", []) or []
    history: List[dict[str, str]] = [
        {"question": q, "answer": a}
        for q, a in zip(questions, answers)
    ]
    last_question = questions[-1] if questions else "Tell me about yourself."
    history.append({"question": last_question, "answer": payload.answer})

    next_question = generate_interview_question(
        history,
        session.get("domain", ""),
        session.get("experience", ""),
        behavior_override=payload.behavior_override,
        resume_context=session.get("resume_context"),
    )

    update_ops = {
        "$push": {"answers": payload.answer},
    }
    if next_question:
        update_ops["$push"]["questions"] = next_question["question"]
        update_ops["$push"]["behaviors"] = next_question["behavior"]

    collection.update_one(
        {"_id": interview_object_id, "user_id": payload.user_id},
        update_ops,
    )
    return {"question": next_question["question"], "behavior": next_question["behavior"]}


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
