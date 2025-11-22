from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

from gtts import gTTS

from config import settings

AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"


def generate_tts_audio(text: str) -> Optional[Path]:
    message = (text or "").strip()
    if not message:
        return None

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.mp3"
    file_path = AUDIO_DIR / filename

    try:
        tts = gTTS(text=message, lang=settings.gtts_language or "en")
        tts.save(str(file_path))
    except Exception:
        return None

    return file_path
