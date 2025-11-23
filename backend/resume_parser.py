import logging
from pathlib import Path
from typing import Optional

from docx import Document
from pypdf import PdfReader

LOGGER = logging.getLogger(__name__)
RESUME_DIR = Path(__file__).resolve().parent / "resumes"
RAW_TEXT_LIMIT = 20000
CONTEXT_LIMIT = 1500


def extract_resume_text(resume_path: Path) -> str:
    if not resume_path.exists():
        return ""

    try:
        suffix = resume_path.suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(str(resume_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        elif suffix == ".docx":
            document = Document(resume_path)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            text = resume_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        LOGGER.warning("Failed to parse resume %s: %s", resume_path, exc)
        return ""

    text = text.strip()
    if len(text) > RAW_TEXT_LIMIT:
        return text[:RAW_TEXT_LIMIT]
    return text


def build_resume_context(text: Optional[str], limit: int = CONTEXT_LIMIT) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) > limit:
        return normalized[:limit]
    return normalized
