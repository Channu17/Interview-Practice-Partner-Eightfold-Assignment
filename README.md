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
4. Visit `http://localhost:8501` and use the Ping API button to verify the FastAPI health endpoint.

## Folder Structure
```
.
├── backend
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── .venv/
├── frontend
│   ├── app.py
│   ├── requirements.txt
│   └── .venv/
├── .env.example
├── .gitignore
└── README.md
```

## Next Steps
- Implement Groq-powered interviewer logic and follow-up flow.
- Add audio capture/playback with Groq speech-to-text and gTTS for responses.
- Persist interview transcripts and feedback notes in MongoDB.
