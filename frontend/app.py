import os
import html
from typing import Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Interview Practice Partner",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none; }
    .hero {
        background: radial-gradient(circle at top, #1f5eff, #111938);
        color: white;
        padding: 2.5rem;
        border-radius: 1.5rem;
        box-shadow: 0 16px 40px rgba(4, 23, 56, 0.35);
        margin-bottom: 1.5rem;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: rgba(255,255,255,0.15);
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-size: 0.85rem;
    }
    .stepper {
        display: flex;
        justify-content: space-between;
        margin: 1.25rem 0 0.5rem;
    }
    .step {
        flex: 1;
        text-align: center;
        color: #8791ad;
        font-size: 0.85rem;
    }
    .step.active { color: #1f5eff; font-weight: 600; }
    .card {
        border-radius: 1rem;
        padding: 1.25rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .chat-window {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 1.25rem;
        padding: 1.1rem;
        max-height: 420px;
        overflow-y: auto;
    }
    .chat-row {
        display: flex;
        margin-bottom: 0.9rem;
    }
    .chat-row.left { justify-content: flex-start; }
    .chat-row.right { justify-content: flex-end; }
    .chat-bubble {
        max-width: 80%;
        padding: 0.75rem 1rem;
        border-radius: 1.2rem;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
        background: #e5e7eb;
        color: #111827;
        border-bottom-left-radius: 0.35rem;
    }
    .chat-bubble.user {
        background: #22c55e;
        color: #052e16;
        border-bottom-left-radius: 1.2rem;
        border-bottom-right-radius: 0.35rem;
    }
    .chat-empty {
        text-align: center;
        color: #94a3b8;
        padding: 2rem 0;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_STATE = {
    "candidate_name": "",
    "resume_option": "without",
    "resume_file_name": "",
    "resume_url": "",
    "resume_present": False,
    "selected_domain_choice": "Sales",
    "custom_domain": "",
    "experience_level": "Intern",
    "current_page": "home",
    "voice_transcript": "",
    "tts_text": "",
    "tts_audio_bytes": b"",
    "user_id": "",
    "use_voice_mode": False,
    "interview_id": "",
    "interview_question": "",
    "last_interview_id": "",
    "answer_input": "",
    "evaluation_feedback": "",
    "feedback_audio_bytes": b"",
    "feedback_audio_source": "",
    "question_audio_bytes": b"",
    "question_audio_source": "",
    "pending_answer_text": None,
    "alert_message": "",
    "alert_level": "info",
}

for key, value in DEFAULT_STATE.items():
    st.session_state.setdefault(key, value)

if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []


def _request_rerun() -> None:
    rerun = getattr(st, "rerun", getattr(st, "experimental_rerun", None))
    if rerun:
        rerun()


def set_alert(message: str, level: str = "info") -> None:
    st.session_state["alert_message"] = message
    st.session_state["alert_level"] = level


def render_alert() -> None:
    message = (st.session_state.get("alert_message") or "").strip()
    level = st.session_state.get("alert_level", "info")
    if not message:
        return
    if level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    elif level == "success":
        st.success(message)
    else:
        st.info(message)
    st.session_state["alert_message"] = ""


def go_to(page: str) -> None:
    st.session_state["current_page"] = page
    _request_rerun()


def upload_resume_file(uploaded_file) -> None:
    if uploaded_file is None:
        return

    with st.spinner("Uploading resume..."):
        try:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                )
            }
            response = requests.post(
                f"{BACKEND_URL}/upload-resume",
                files=files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Failed to upload resume: {exc}")
            return

    data = response.json()
    st.session_state["resume_file_name"] = uploaded_file.name
    st.session_state["resume_url"] = data.get("resume_url", "")
    st.session_state["resume_present"] = bool(st.session_state["resume_url"])
    if st.session_state["resume_url"]:
        st.success("Resume uploaded successfully.")


def transcribe_voice_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    with st.spinner("Transcribing voice clip..."):
        try:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "audio/mpeg",
                )
            }
            response = requests.post(
                f"{BACKEND_URL}/voice-to-text",
                files=files,
                timeout=60,
            )
            response.raise_for_status()
            transcript = response.json().get("transcript", "").strip()
            st.session_state["voice_transcript"] = transcript
            return transcript
        except requests.RequestException as exc:
            st.error(f"Failed to transcribe audio: {exc}")
            return ""


def synthesize_text_to_voice(text: str, state_key: Optional[str] = "tts_audio_bytes") -> bytes:
    message = (text or "").strip()
    if not message:
        return b""

    with st.spinner("Generating audio reply..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/text-to-voice",
                json={"text": message},
                timeout=60,
            )
            response.raise_for_status()
            if state_key:
                st.session_state[state_key] = response.content
            return response.content
        except requests.RequestException as exc:
            st.error(f"Failed to generate voice: {exc}")
            return b""


def _resolve_domain_label() -> str:
    choice = (st.session_state.get("selected_domain_choice") or "Sales").strip()
    custom = (st.session_state.get("custom_domain") or "").strip()
    if choice == "Other" and custom:
        return custom
    return choice or "Sales"


def get_user_identifier() -> str:
    stored_id = (st.session_state.get("user_id") or "").strip()
    if stored_id:
        return stored_id
    fallback = (st.session_state.get("candidate_name") or "").strip()
    return fallback or "guest-user"


def register_user_profile() -> bool:
    name = (st.session_state.get("candidate_name") or "").strip()
    if not name:
        st.warning("Please enter your name before continuing.")
        return False

    payload = {
        "name": name,
        "resume_present": bool(st.session_state.get("resume_url")),
        "resume_url": st.session_state.get("resume_url") or None,
        "domain": _resolve_domain_label(),
        "experience": st.session_state.get("experience_level", "Intern"),
    }

    with st.spinner("Saving your profile..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/register-user",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Unable to register: {exc}")
            return False

    user_id = (response.json().get("user_id") or "").strip()
    if not user_id:
        st.error("Registration succeeded but no user id was returned.")
        return False

    st.session_state["user_id"] = user_id
    st.success("Profile stored. Next, configure your practice domain.")
    return True


def start_mock_interview() -> None:
    user_id = get_user_identifier()
    if not st.session_state.get("user_id"):
        st.warning("Please register on the previous step before starting an interview.")
        return
    payload = {
        "user_id": user_id,
        "domain": _resolve_domain_label(),
        "experience": st.session_state.get("experience_level", "Intern"),
    }

    with st.spinner("Starting interview..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/start-interview",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Unable to start interview: {exc}")
            return

    data = response.json()
    question = data.get("question", "").strip()
    st.session_state["interview_id"] = data.get("interview_id", "")
    st.session_state["interview_question"] = question
    st.session_state["qa_history"] = []
    st.session_state["pending_answer_text"] = ""
    st.session_state["evaluation_feedback"] = ""
    st.session_state["feedback_audio_bytes"] = b""
    st.session_state["feedback_audio_source"] = ""
    st.session_state["question_audio_bytes"] = b""
    st.session_state["question_audio_source"] = ""
    if question:
        set_alert("Interview started. First question is ready.", "success")
        ensure_question_audio(question)
    _request_rerun()


def submit_answer_to_mock_interview(answer: str) -> None:
    text = (answer or "").strip()
    if not text:
        st.warning("Add an answer before submitting.")
        return

    interview_id = st.session_state.get("interview_id")
    if not interview_id:
        st.warning("Start an interview first.")
        return

    payload = {
        "interview_id": interview_id,
        "user_id": get_user_identifier(),
        "answer": text,
    }

    with st.spinner("Submitting answer..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/process-answer",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Unable to process answer: {exc}")
            return

    next_question = response.json().get("question", "").strip()
    st.session_state.setdefault("qa_history", [])
    st.session_state["qa_history"].append(
        {
            "question": st.session_state.get("interview_question", ""),
            "answer": text,
        }
    )
    st.session_state["interview_question"] = next_question
    st.session_state["pending_answer_text"] = ""
    set_alert("Answer logged. Awaiting the next prompt.")
    if not next_question:
        set_alert("No further questions returned. End the interview to fetch feedback.", "warning")
    else:
        ensure_question_audio(next_question)
    _request_rerun()


def complete_mock_interview() -> None:
    interview_id = st.session_state.get("interview_id")
    if not interview_id:
        st.warning("No active interview to end.")
        return

    payload = {
        "interview_id": interview_id,
        "user_id": get_user_identifier(),
    }

    with st.spinner("Generating evaluation..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/end-interview",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Unable to end interview: {exc}")
            return

    feedback = response.json().get("feedback", "").strip()
    st.session_state["evaluation_feedback"] = feedback or "Thanks for completing the mock interview."
    st.session_state["last_interview_id"] = interview_id
    st.session_state["interview_id"] = ""
    st.session_state["interview_question"] = ""
    st.session_state["pending_answer_text"] = None
    st.session_state["feedback_audio_bytes"] = b""
    st.session_state["feedback_audio_source"] = ""
    st.session_state["question_audio_bytes"] = b""
    st.session_state["question_audio_source"] = ""
    set_alert("Evaluator feedback ready.", "success")
    ensure_feedback_audio(st.session_state["evaluation_feedback"])
    _request_rerun()


def ensure_question_audio(question: str) -> None:
    question_text = (question or "").strip()
    if not question_text or not st.session_state.get("use_voice_mode"):
        return
    if st.session_state.get("question_audio_source") == question_text:
        return
    audio_bytes = synthesize_text_to_voice(question_text, state_key="question_audio_bytes")
    if audio_bytes:
        st.session_state["question_audio_source"] = question_text


def ensure_feedback_audio(feedback: str) -> None:
    summary = (feedback or "").strip()
    if not summary or not st.session_state.get("use_voice_mode"):
        return
    if st.session_state.get("feedback_audio_source") == summary:
        return
    audio_bytes = synthesize_text_to_voice(summary, state_key="feedback_audio_bytes")
    if audio_bytes:
        st.session_state["feedback_audio_source"] = summary


def _format_bubble_text(text: str) -> str:
    if not text:
        return "&nbsp;"
    escaped = html.escape(text.strip())
    return escaped.replace("\n", "<br/>") or "&nbsp;"


def _chat_row_html(text: str, side: str) -> str:
    bubble_class = "chat-bubble user" if side == "right" else "chat-bubble"
    row_class = "chat-row right" if side == "right" else "chat-row left"
    return f"<div class='{row_class}'><div class='{bubble_class}'>{_format_bubble_text(text)}</div></div>"


def render_chat_history(history, pending_question: str) -> None:
    blocks = ["<div class='chat-window'>"]
    has_rows = False

    for turn in history:
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()
        if question:
            blocks.append(_chat_row_html(question, "left"))
            has_rows = True
        if answer:
            blocks.append(_chat_row_html(answer, "right"))
            has_rows = True

    pending_question = (pending_question or "").strip()
    if pending_question:
        last_question = (history[-1].get("question", "") if history else "").strip()
        if pending_question != last_question:
            blocks.append(_chat_row_html(pending_question, "left"))
            has_rows = True

    if not has_rows:
        blocks.append("<div class='chat-empty'>No messages yet. Start the interview to receive questions.</div>")

    blocks.append("</div>")
    st.markdown("\n".join(blocks), unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="pill">🎯 Your agentic mock interviewer</div>
            <h1 style="margin-top: 0.6rem;">Interview Practice Partner</h1>
            <p style="opacity:0.9; margin-bottom:1.2rem;">
                Run lifelike mock interviews with dynamic follow-ups, voice-ready flows, and actionable feedback insights.
                Choose roles, test scenarios, and refine every response with confidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="stepper">
            <span class="step active">1 · Profile</span>
            <span class="step">2 · Domain</span>
            <span class="step">3 · Interview</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Get Started", use_container_width=True):
        go_to("user_info")


def render_user_info() -> None:
    st.button("← Back", on_click=go_to, args=("home",), key="back_home")
    st.title("Tell us about you")
    st.caption("We’ll personalize prompts and follow-ups based on your profile.")

    name = st.text_input(
        "Full Name",
        value=st.session_state["candidate_name"],
        placeholder="Alex Candidate",
    )
    st.session_state["candidate_name"] = name

    options = ["Continue with Resume", "Continue without Resume"]
    resume_choice = st.radio(
        "How would you like to proceed?",
        options,
        index=0 if st.session_state["resume_option"] == "with" else 1,
    )
    st.session_state["resume_option"] = "with" if resume_choice == options[0] else "without"

    if st.session_state["resume_option"] == "with":
        uploaded_file = st.file_uploader(
            "Upload resume",
            type=["pdf", "docx"],
            key="resume_uploader",
        )
        if uploaded_file is not None:
            should_upload = uploaded_file.name != st.session_state["resume_file_name"]
            if should_upload:
                upload_resume_file(uploaded_file)
        if st.session_state["resume_url"]:
            st.info(f"Stored resume reference: {st.session_state['resume_file_name']}")
    else:
        st.session_state["resume_file_name"] = ""
        st.session_state["resume_url"] = ""
        st.session_state["resume_present"] = False

    if st.button("Next", use_container_width=True, key="user_next"):
        if register_user_profile():
            go_to("domain")

    if st.session_state.get("user_id"):
        st.caption(f"Registered user id: {st.session_state['user_id']}")


def render_domain_selection() -> None:
    st.button("← Back", on_click=go_to, args=("user_info",), key="back_user")
    st.title("Pick your practice domain")
    st.caption("Preview upcoming interview packs and plan your practice journey.")

    domain_options = [
        "Sales",
        "Python Developer",
        "Full Stack Developer",
        "Data Science",
        "Other",
    ]

    current_choice = st.session_state["selected_domain_choice"]
    if current_choice not in domain_options:
        current_choice = domain_options[0]

    domain_choice = st.radio(
        "Choose a domain",
        domain_options,
        index=domain_options.index(current_choice),
    )

    custom_role = st.session_state["custom_domain"]
    if domain_choice == "Other":
        custom_role = st.text_input(
            "Tell us about the role",
            value=custom_role,
            placeholder="e.g., Customer Success Lead",
        )
    else:
        custom_role = ""

    experience_levels = ["Intern", "Fresher", "Medium", "Senior"]
    current_experience = st.session_state["experience_level"]
    if current_experience not in experience_levels:
        current_experience = experience_levels[0]

    experience_choice = st.radio(
        "Experience level",
        experience_levels,
        index=experience_levels.index(current_experience),
    )

    if st.button("Next", use_container_width=True, key="domain_next"):
        if not st.session_state.get("user_id"):
            st.warning("Please register on the previous step before continuing.")
        else:
            st.session_state["selected_domain_choice"] = domain_choice
            st.session_state["custom_domain"] = custom_role
            st.session_state["experience_level"] = experience_choice
            st.session_state["qa_history"] = []
            st.session_state["evaluation_feedback"] = ""
            go_to("interview")


def render_interview_session() -> None:
    st.button("← Back", on_click=go_to, args=("domain",), key="back_to_domain")
    st.title("Interview Playground")
    st.caption("Answer in a chat-style flow, then let the evaluator summarize your run.")

    summary_role = _resolve_domain_label()
    st.info(f"Practicing for {summary_role} • Experience: {st.session_state.get('experience_level', 'Intern')}")

    voice_mode = st.toggle(
        "Voice mode (speak & listen)",
        value=st.session_state.get("use_voice_mode", False),
        key="voice_mode_toggle",
        help="Switch on to upload spoken answers and hear the interviewer and evaluator.",
    )
    st.session_state["use_voice_mode"] = voice_mode
    render_alert()

    interview_active = bool(st.session_state.get("interview_id"))
    current_question = (st.session_state.get("interview_question") or "").strip() if interview_active else ""
    history = st.session_state.get("qa_history", [])

    if voice_mode and current_question:
        ensure_question_audio(current_question)

    st.subheader("Chat history")
    render_chat_history(history, current_question if interview_active else "")

    if interview_active and voice_mode and st.session_state.get("question_audio_bytes"):
        st.audio(st.session_state["question_audio_bytes"], format="audio/mp3")

    if interview_active:
        st.subheader("Your response")
        pending_answer = st.session_state.get("pending_answer_text")
        if pending_answer is not None:
            st.session_state["answer_input"] = pending_answer
            st.session_state["pending_answer_text"] = None

        st.text_area(
            "Message",
            key="answer_input",
            height=140,
            placeholder="Type your reply or drop in the transcription before sending...",
        )

        voice_upload = None
        if voice_mode:
            st.caption("🎙️ Voice reply (optional)")
            voice_upload = st.file_uploader(
                "Upload your audio response",
                type=["mp3", "wav", "m4a", "webm"],
                key="voice_answer_uploader",
            )

        send_col, finish_col, mic_col = st.columns([3, 2, 1])
        send_clicked = False
        with send_col:
            send_clicked = st.button("Send", use_container_width=True, key="send_answer_btn")
        with finish_col:
            if st.button("Finish", use_container_width=True, key="finish_interview_btn"):
                complete_mock_interview()
        mic_clicked = False
        with mic_col:
            if voice_mode:
                mic_clicked = st.button("🎙️", use_container_width=True, key="transcribe_answer_btn")

        if send_clicked:
            submit_answer_to_mock_interview(st.session_state.get("answer_input", ""))

        if mic_clicked:
            if voice_upload is None:
                set_alert("Upload an audio file before transcribing.", "warning")
            else:
                transcript = transcribe_voice_file(voice_upload)
                if transcript:
                    st.session_state["pending_answer_text"] = transcript
                    set_alert("Transcript captured. Review and press Send.", "success")
                    _request_rerun()
        elif voice_mode and voice_upload is None:
            st.caption("Select an audio clip above, then tap 🎙️ to transcribe it into the chat box.")
    else:
        st.info("No active session yet. Start when you're ready to practice.")
        if not st.session_state.get("user_id"):
            st.warning("Please complete profile + domain setup first.")
        if st.button("Start interview", use_container_width=True, key="start_interview_btn"):
            start_mock_interview()

    feedback = (st.session_state.get("evaluation_feedback") or "").strip()
    if feedback:
        st.divider()
        st.subheader("Evaluator feedback")
        st.write(feedback)
        if voice_mode:
            ensure_feedback_audio(feedback)
        else:
            if st.button("Convert feedback to audio", key="convert_feedback_audio"):
                synthesize_text_to_voice(feedback, state_key="feedback_audio_bytes")
                st.session_state["feedback_audio_source"] = feedback
        if st.session_state.get("feedback_audio_bytes"):
            st.audio(st.session_state["feedback_audio_bytes"], format="audio/mp3")
        if st.session_state.get("last_interview_id"):
            st.caption(f"Last evaluated session id: {st.session_state['last_interview_id']}")


page = st.session_state["current_page"]

if page == "home":
    render_home()
elif page == "user_info":
    render_user_info()
elif page == "domain":
    render_domain_selection()
else:
    render_interview_session()
