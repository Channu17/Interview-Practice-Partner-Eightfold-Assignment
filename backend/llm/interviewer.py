from __future__ import annotations

from typing import Iterable, List, Optional

from groq import Groq

from config import settings

DEFAULT_MODEL = "exmeta-llama/llama-prompt-guard-2-86m"
FALLBACK_QUESTION = "Could you walk me through a project you're proud of?"

_client: Optional[Groq] = None


def _get_client() -> Optional[Groq]:
    global _client
    if _client is None and settings.groq_api_key:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


SYSTEM_PROMPT = (
    "You are a professional job interviewer conducting mock interviews."
    " Keep questions concise, grounded in the candidate's domain and experience level."
    " Encourage clarity if the user seems confused, stay focused if they go off-topic,"
    " and politely redirect overly chatty responses back to the role."
    " When answers are weak or vague, ask for specific examples or quantifiable impact."
    " Avoid sharing solutions; keep the conversation realistic and supportive."
)


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


def generate_interview_question(
    history: Iterable[dict[str, str]],
    domain: str,
    experience: str,
) -> str:
    """Return the next interview question based on conversation history."""

    client = _get_client()
    if client is None:
        return FALLBACK_QUESTION

    history_text = _history_to_text(history)
    user_message = (
        "Interview context:\n"
        f"- Role/Domain: {domain or 'General'}\n"
        f"- Experience: {experience or 'Unspecified'}\n"
        "\nConversation so far:\n"
        f"{history_text}\n\n"
        "Produce the next single interview question."
        " Tailor it to the candidate's background."
        " Address confused users by clarifying requirements, keep efficient users moving,"
        " and redirect off-topic remarks politely back to the interview."
        " If answers are invalid or empty, ask them to elaborate.")

    try:
        response = client.chat.completions.create(
            model=settings.groq_model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        return content or FALLBACK_QUESTION
    except Exception:
        return FALLBACK_QUESTION
