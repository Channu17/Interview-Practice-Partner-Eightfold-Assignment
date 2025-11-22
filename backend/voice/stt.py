from __future__ import annotations

from typing import Optional

from groq import Groq

from config import settings

SPEECH_MODEL = "whisper-large-v3"
_client: Optional[Groq] = None


def _get_client() -> Optional[Groq]:
    global _client
    if _client is None and settings.groq_api_key:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    mime_type: Optional[str] = None,
) -> str:
    client = _get_client()
    if client is None or not file_bytes:
        return ""

    try:
        response = client.audio.transcriptions.create(
            model=SPEECH_MODEL,
            file=(filename or "audio.mp3", file_bytes, mime_type or "audio/mpeg"),
            response_format="json",
        )
        text = getattr(response, "text", "")
        if not text and isinstance(response, dict):
            text = response.get("text", "")
        return text.strip()
    except Exception:
        return ""
