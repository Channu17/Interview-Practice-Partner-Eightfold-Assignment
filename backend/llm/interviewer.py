from __future__ import annotations

import json
import logging
from typing import Iterable, List, Optional, TypedDict, Literal

from groq import Groq

from config import settings

DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_QUESTION = "Could you walk me through a project you're proud of?"
BehaviorCategory = Literal[
    "Confused User",
    "Efficient User",
    "Chatty User",
    "Edge-Case User",
]


class QuestionResult(TypedDict):
    question: str
    behavior: BehaviorCategory


DEFAULT_BEHAVIOR: BehaviorCategory = "Efficient User"

_client: Optional[Groq] = None
logger = logging.getLogger(__name__)


def _get_client() -> Optional[Groq]:
    global _client
    if _client is None and settings.groq_api_key:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


SYSTEM_PROMPT = (
    "You are a professional interviewer conducting mock technical and behavioral sessions."
    " Behavior categories: Confused User (uncertain or off-track), Efficient User (short and focused),"
    " Chatty User (long rambles, stories), Edge-Case User (invalid, malicious, or testing limits)."
    " Review the latest candidate answer, classify their behavior, and craft the next question using these rules:"
    " Confused → simplify, offer hints, and politely clarify;"
    " Efficient → be direct and move fast;"
    " Chatty → summarize and steer back on-topic;"
    " Edge-Case → respond safely and redirect to the interview."
    " Always keep questions grounded in the stated role and experience, avoid giving away solutions,"
    " and answer ONLY with valid JSON: {\"behavior\": \"<category>\", \"question\": \"<next question>\"}."
)


BEHAVIOR_ALIASES: dict[str, BehaviorCategory] = {
    "confused": "Confused User",
    "confused user": "Confused User",
    "confused-user": "Confused User",
    "efficient": "Efficient User",
    "efficient user": "Efficient User",
    "efficient-user": "Efficient User",
    "chatty": "Chatty User",
    "chatty user": "Chatty User",
    "chatty-user": "Chatty User",
    "edge": "Edge-Case User",
    "edge case": "Edge-Case User",
    "edge-case": "Edge-Case User",
    "edge-case user": "Edge-Case User",
    "edge case user": "Edge-Case User",
}


def _history_to_text(history: Iterable[dict[str, str]]) -> str:
    lines: List[str] = []
    for turn in history:
        question = turn.get("question", "").strip()
        answer = turn.get("answer", "").strip()
        if not question:
            continue
        answer_text = answer or "(no answer provided)"
        lines.append(f"Q: {question}\nA: {answer_text}")
    return "\n\n".join(lines) if lines else "No prior questions."


def _normalize_behavior_label(value: Optional[str]) -> Optional[BehaviorCategory]:
    if not value:
        return None
    key = value.strip().lower()
    return BEHAVIOR_ALIASES.get(key)


def _attempt_json_load(payload: str) -> dict:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = payload[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                return {}
    return {}


def _parse_question_result(content: str) -> QuestionResult:
    data = _attempt_json_load(content)
    question = (data.get("question") or "").strip()
    behavior = _normalize_behavior_label(data.get("behavior")) or DEFAULT_BEHAVIOR
    if not question:
        question = FALLBACK_QUESTION
    return {
        "question": question,
        "behavior": behavior,
    }


def generate_interview_question(
    history: Iterable[dict[str, str]],
    domain: str,
    experience: str,
    behavior_override: Optional[str] = None,
    resume_context: Optional[str] = None,
) -> QuestionResult:
    """Return the next interview question and detected behavior."""

    turns = list(history)
    client = _get_client()
    normalized_override = _normalize_behavior_label(behavior_override)

    if client is None:
        logger.warning("Groq client not configured; returning fallback question")
        return {
            "question": FALLBACK_QUESTION,
            "behavior": normalized_override or DEFAULT_BEHAVIOR,
        }

    history_text = _history_to_text(turns)
    resume_block = (
        "Resume highlights:\n"
        f"{resume_context}\n\n"
        if resume_context
        else ""
    )
    latest_answer = (turns[-1].get("answer", "").strip() if turns else "")
    behavior_hint = (
        f"\nDemo override: Treat this candidate as {normalized_override} regardless of the latest answer."
        if normalized_override
        else ""
    )
    user_message = (
        "Interview context:\n"
        f"- Role/Domain: {domain or 'General'}\n"
        f"- Experience: {experience or 'Unspecified'}\n"
        f"{resume_block}"
        "\nConversation so far:\n"
        f"{history_text}\n\n"
        "Latest candidate answer:\n"
        f"{latest_answer or '(no answer yet; start the session)'}\n\n"
        "Determine user behavior category from the answer and tailor the next question accordingly."
        f"{behavior_hint}\n"
        "Remember to reply ONLY with JSON containing 'behavior' and 'question'."
    )

    try:
        response = client.chat.completions.create(
            model=settings.groq_model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.35,
            max_tokens=220,
        )
        content = response.choices[0].message.content.strip()
        parsed = _parse_question_result(content)
        if normalized_override:
            parsed["behavior"] = normalized_override
        return parsed
    except Exception as exc:
        logger.exception("Groq question generation failed: %s", exc)
        return {
            "question": FALLBACK_QUESTION,
            "behavior": normalized_override or DEFAULT_BEHAVIOR,
        }
