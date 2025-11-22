# Interview Practice Partner

Agentic mock-interview assistant focused on conversation quality. Stage 1 delivers the project skeleton so we can plug in LLM, Groq voice, MongoDB storage, and Streamlit UI in later stages.

## Tech Stack
- Streamlit frontend with gTTS playback hooks
- FastAPI backend with Pydantic config helpers
- MongoDB Atlas (via `pymongo`) for storing sessions
- Groq LLM + speech APIs
- Python virtual environments for isolated dependencies

## Getting Started
1. Copy `.env.example` to `.env` in both `backend/` and `frontend/` roots (or load globally) and fill in MongoDB and Groq secrets.
2. Backend setup:
	```bash
	cd backend
	source .venv/Scripts/activate
	pip install -r requirements.txt  # already run once
	uvicorn main:app --reload --host ${BACKEND_HOST:-0.0.0.0} --port ${BACKEND_PORT:-8000}
	```
3. Frontend setup:
	```bash
	cd frontend
	source .venv/Scripts/activate
	pip install -r requirements.txt  # already run once
	streamlit run app.py --server.port 8501
	```
4. Visit `http://localhost:8501` to use the Streamlit flow. Make sure `GROQ_API_KEY` is set so the interviewer can fetch new questions from Groq.

## Folder Structure
```
.
├── backend
│   ├── config.py
│   ├── db/
│   ├── llm/
│   ├── audio/
│   ├── main.py
│   ├── models/
│   ├── requirements.txt
│   ├── resumes/
│   └── routes/
├── frontend
│   ├── app.py
│   └── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Next Steps
- Route the Streamlit frontend through the new interview APIs and surface the Groq-generated dialogue.
- Layer in voice capture/playback (Groq speech + gTTS) for the preferred interaction mode.
- Expand feedback storage to highlight strengths, growth areas, and recommended practice paths.

## Voice Mode Endpoints
- `POST /voice-to-text`: Upload MP3/WAV audio to transcribe speech via Groq's Whisper-based API.
- `POST /text-to-voice`: Provide text to receive an MP3 synthesized with gTTS, ready for playback in the frontend.
