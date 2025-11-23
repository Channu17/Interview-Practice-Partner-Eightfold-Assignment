# Interview Practice Partner

AI-powered mock interviews with adaptive questioning, voice support, and candid evaluator feedback for every practice run.

## Repository Access

- **GitHub:** https://github.com/Channu17/Interview-Practice-Partner-Eightfold-Assignment 
- **Codebase:** Backend (`backend/`) FastAPI + MongoDB services, Frontend (`frontend/`) Streamlit conversational UI

## Why This Exists

Interview loops rarely offer fast feedback. This project simulates an interviewer that:

- Tailors questions to a candidate’s resume, target domain, and experience band
- Adapts tone/behavior after every answer (confused, efficient, chatty, edge-case)
- Supports voice I/O (Whisper for STT, gTTS for TTS) in addition to chat
- Stores transcripts and generates actionable critique via a dedicated evaluator agent

## Feature Highlights

- 🔐 **Profile + Resume ingestion** – upload PDF/DOCX resumes, auto-summarize context
- 🧠 **LLM interviewer** – Groq-hosted Llama models keep questions human, short, and non-repetitive
- 🎤 **Voice bridge** – optional inline recorder, Whisper transcription, and audio playback for questions + feedback
- 📊 **Evaluator agent** – closes each session with structured coaching and a verdict
- 🗂️ **Mongo persistence** – tracks users, interviews, behaviors, and generated feedback for retrospection

## Architecture Notes

```
┌─────────────┐    HTTPS     ┌───────────────────────────────┐
│ Streamlit   │────────────▶│ FastAPI backend (uvicorn)      │
│ frontend    │◀────────────│ /routes/{users,interview,voice}│
└─────────────┘  JSON/Audio  └────────────┬──────────────────┘
	  │                               │
	  │voice clips / playback          │Mongo queries + Groq calls
	  ▼                               ▼
  Whisper STT via                     MongoDB Atlas / local
  Groq API (voice/stt.py)             (db/mongo.py)
	  │                               ▲
	  │text prompts                  │
	  └────────► Llama interviewer + evaluator (llm/*)
```

- **Frontend:** Multi-page Streamlit state machine (`frontend/app.py`) orchestrates onboarding, domain selection, interview chat, and evaluator review.
- **Backend:** FastAPI (`backend/main.py`) exposes profile, interview, and voice endpoints; CORS enabled for local dev.
- **AI Layer:** `llm/interviewer.py` keeps short JSON responses, retries duplicates, and respects behavior overrides; `llm/evaluator.py` provides concise feedback.
- **Resume Parsing:** `resume_parser.py` normalizes PDF/DOCX input for prompt grounding.
- **Voice:** `voice/stt.py` hits Groq Whisper, `voice/tts.py` uses gTTS for lightweight speech synthesis.

## Design Decisions

1. **Two-agent approach:** Separation between interviewing and evaluation simplifies prompts and mirrors real interview loops.
2. **MongoDB over SQL:** Document structure maps naturally to nested Q/A histories and behavior flags without joins.
3. **Stateless HTTP + client state:** Streamlit keeps UI/voice state client-side, enabling simple FastAPI deployment.
4. **Groq APIs:** Provides low-latency Llama + Whisper access with JSON-only guardrails to avoid brittle parsing.
5. **gTTS fallback:** Offers cost-free speech synthesis when Groq voices are unavailable.

## Environment Configuration

Create `.env` files in both `backend/` and `frontend/`:

`backend/.env`
```
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=interview_practice
GROQ_API_KEY=sk-...
GROQ_MODEL=llama-3.1-8b-instant
GROQ_VOICE=alloy
GTTS_LANGUAGE=en
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

`frontend/.env`
```
BACKEND_URL=http://localhost:8000
```

## Local Setup

Prerequisites: Python 3.10+, MongoDB (local or Atlas), FFmpeg (recommended for audio), Node not required.

```bash
git clone https://github.com/Channu17/Interview-Practice-Partner-Eightfold-Assignment.git
cd Interview-Practice-Partner-Eightfold-Assignment
```

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate  # On PowerShell use .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Key endpoints:

- `POST /register-user` – save profile + parsed resume context
- `POST /upload-resume` – accept PDF/DOC/DOCX, store reference in `resumes/`
- `POST /start-interview` – create interview session, generate personalized opener
- `POST /process-answer` – log answers, fetch next adaptive question
- `POST /end-interview` – finalize session, trigger evaluator feedback
- `POST /voice-to-text` / `POST /text-to-voice` – voice utilities

### Frontend (Streamlit)

```bash
cd frontend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py
```

Set `BACKEND_URL` to your FastAPI instance. The UI guides users through profile → domain → interview → feedback, and toggles voice features on demand.

## Codebase Guide

- `backend/routes/` – REST boundaries for users, interview loop, and voice helpers
- `backend/llm/` – interviewer + evaluator agents (Groq integration, retries, formatting)
- `backend/voice/` – Whisper transcription + gTTS synthesis wrappers
- `backend/models/` – Pydantic schemas for persistence and validation
- `frontend/app.py` – all Streamlit pages, state transitions, and voice controls
- `resumes/` & `audio/` – temp storage for uploaded resumes + generated MP3s (gitignored)

## Testing & Next Steps

- Use `curl http://localhost:8000/health` to confirm backend readiness
- Seed Mongo with mock users or clear via `db.drop_collection("interviews")` between runs
- Extend `routes/interview.py` to add guardrails (max turns, timeouts) before productionizing