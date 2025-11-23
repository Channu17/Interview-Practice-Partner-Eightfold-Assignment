from __future__ import annotations

import json
import logging
import secrets
from typing import Iterable, List, Optional, TypedDict, Literal

from groq import Groq

from config import settings

DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_QUESTION = "Could you walk me through a project you're proud of?"
MAX_GENERATION_ATTEMPTS = 3
MAX_HISTORY_TURNS = 6
MAX_ASKED_TRACK = 12
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
    "You are a warm yet incisive interviewer facilitating mock sessions."
    " Always sound human—acknowledge what the candidate just shared, avoid robotic phrasing, and keep responses under three sentences."
    " Persona definitions you must classify every turn into:"
    " Confused User (uncertain, contradictory, or asking meta questions),"
    " Efficient User (direct, wants fast pacing),"
    " Chatty User (storytelling, tangents),"
    " Edge-Case User (testing limits, off-topic, malicious, or requesting unsupported actions)."
    " Adapt the next question accordingly:"
    " Confused → gently clarify intent, hint at structure, and simplify wording;"
    " Efficient → acknowledge brevity and move straight to a challenging follow-up;"
    " Chatty → summarize the useful part, kindly steer back to the role;"
    " Edge-Case → keep safety first, decline risky requests, and redirect to the interview scope."
    " Never repeat a previous question verbatim, and whenever the session stage is 'opening' you must greet the candidate by name, mention the role, and set expectations before asking anything else."
    " Respond ONLY with valid JSON shaped like {\"behavior\": \"<category>\", \"question\": \"<next question>\"}."
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


def _should_retry(question: str, asked_questions: List[str]) -> bool:
    normalized = (question or "").strip()
    if not normalized:
        return True
    if normalized == FALLBACK_QUESTION:
        return True
    if normalized in asked_questions:
        return True
    return False


def generate_interview_question(
    history: Iterable[dict[str, str]],
    domain: str,
    experience: str,
    behavior_override: Optional[str] = None,
    resume_context: Optional[str] = None,
    candidate_name: Optional[str] = None,
) -> QuestionResult:
    """Return the next interview question and detected behavior."""

    turns = list(history)[-MAX_HISTORY_TURNS:]
    client = _get_client()
    normalized_override = _normalize_behavior_label(behavior_override)
    session_stage = "opening" if not turns else "follow-up"
    asked_questions = [
        (turn.get("question") or "").strip()
        for turn in turns
        if (turn.get("question") or "").strip()
    ][-MAX_ASKED_TRACK:]
    asked_block = "\n".join(f"- {question}" for question in asked_questions) or "- None yet"
    variation_token = secrets.token_hex(3)

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
    provided_name = (candidate_name or "").strip() or "Unknown"
    behavior_hint = (
        f"\nDemo override: Treat this candidate as {normalized_override} regardless of the latest answer."
        if normalized_override
        else ""
    )
    base_user_message = (
        "Interview context:\n"
        f"- Role/Domain: {domain or 'General'}\n"
        f"- Experience: {experience or 'Unspecified'}\n"
        f"- Candidate name: {provided_name}\n"
        f"{resume_block}"
        f"- Session stage: {session_stage}\n"
        "- Previously asked questions (do NOT repeat verbatim):\n"
        f"{asked_block}\n"
        f"- Variation token (use as creative inspiration so openings differ each run): {variation_token}\n"
        "\nConversation so far:\n"
        f"{history_text}\n\n"
        "Latest candidate answer:\n"
        f"{latest_answer or '(no answer yet; start the session)'}\n\n"
        "Guidelines:\n"
        "1. If stage is opening, welcome the candidate by name, mention the role, and state how the interview will flow before posing the first question.\n"
        "2. If stage is follow-up, briefly reflect or acknowledge their previous answer before asking the next question.\n"
        "3. Sound human—mix pacing, avoid repetitive templates, and keep it under three sentences.\n"
        "4. Enforce behavior-specific handling per the system prompt, especially for Edge-Case inputs.\n"
        "5. Never leak the JSON requirement—respond only with valid JSON containing 'behavior' and 'question'."
        f"{behavior_hint}\n"
        "Remember to reply ONLY with JSON containing 'behavior' and 'question'."
    )

    last_error: Optional[Exception] = None
    attempt_hint = ""
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            user_message = base_user_message + attempt_hint
            response = client.chat.completions.create(
                model=settings.groq_model or DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.55,
                max_tokens=220,
            )
            content = response.choices[0].message.content.strip()
            parsed = _parse_question_result(content)
            if normalized_override:
                parsed["behavior"] = normalized_override
            if _should_retry(parsed.get("question", ""), asked_questions) and attempt < MAX_GENERATION_ATTEMPTS:
                logger.warning(
                    "Retrying question generation (attempt %s) due to invalid/duplicate output", attempt
                )
                duplicate = (parsed.get("question") or "").strip() or "(empty output)"
                attempt_hint = (
                    "\nCritical reminder: the previous completion repeated "
                    f"'{duplicate}'. Provide a NEW, distinct question not in the asked list above."
                )
                continue
            return parsed
        except Exception as exc:
            last_error = exc
            logger.exception("Groq question generation failed on attempt %s: %s", attempt, exc)

    return {
        "question": FALLBACK_QUESTION,
        "behavior": normalized_override or DEFAULT_BEHAVIOR,
    }
