from __future__ import annotations

import logging
from typing import Iterable, List, Optional

from groq import Groq

from config import settings

DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_FEEDBACK = (
    "Interview feedback is temporarily unavailable. Please retry once the evaluator comes back online."
)

_client: Optional[Groq] = None
logger = logging.getLogger(__name__)


def _get_client() -> Optional[Groq]:
    global _client
    if _client is None and settings.groq_api_key:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


EVALUATOR_SYSTEM_PROMPT = (
    "You are a bar-raising technical interviewer who delivers candid, detail-rich critiques. "
    "Call out weak or incomplete answers, note any risk areas for the role, and balance brief praise with actionable criticism."
)


def _history_to_text(history: Iterable[dict[str, str]]) -> str:
    lines: List[str] = []
    for idx, turn in enumerate(history, start=1):
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()
        if not question and not answer:
            continue
        question_text = question or "(question unavailable)"
        answer_text = answer or "(no answer provided)"
        lines.append(f"Question {idx}: {question_text}\nAnswer: {answer_text}")
    return "\n\n".join(lines) if lines else "No interview responses were captured."


def evaluate_interview(
    history: Iterable[dict[str, str]],
    domain: str,
    experience: str,
) -> str:
    """Summarize the interview with structured, plain-text coaching feedback."""

    client = _get_client()
    if client is None:
        logger.warning("Groq client not configured; returning fallback feedback")
        return FALLBACK_FEEDBACK

    history_text = _history_to_text(history)
    user_message = (
        "Interview evaluation request.\n"
        f"Target role / domain: {domain or 'Generalist'}\n"
        f"Experience level: {experience or 'Unspecified'}\n\n"
        "Conversation transcript:\n"
        f"{history_text}\n\n"
        "Produce brief plain-text paragraphs (no bullet lists) that cover:\n"
        "- Communication quality (note hesitations or fluff).\n"
        "- Technical depth relative to the stated role; highlight any gaps or missing fundamentals.\n"
        "- Observed confidence/executive presence plus listening skills.\n"
        "- Structure & clarity of explanations, including any rambling or unanswered prompts.\n"
        "- 3 pointed improvement actions (skills, preparation, delivery).\n"
        "- Final summary verdict such as 'Overall: Needs Work (5/10)' with a short justification.\n"
        "Adopt a stricter coaching tone: be professional but frank, emphasize shortcomings before strengths, and keep the response under ~180 words without markdown tables."
    )

    try:
        response = client.chat.completions.create(
            model=settings.groq_model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=350,
        )
        content = response.choices[0].message.content.strip()
        return content or FALLBACK_FEEDBACK
    except Exception as exc:
        logger.exception("Groq evaluation failed: %s", exc)
        return FALLBACK_FEEDBACK
