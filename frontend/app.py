import os
import base64
from typing import Optional

import requests
import streamlit as st
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Interview Practice Partner",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEFAULT_STATE = {
    "candidate_name": "",
    "resume_option": "without",
    "resume_file_name": "",
    "resume_url": "",
    "resume_present": False,
    "selected_domain_choice": "Agentic AI",
    "custom_domain": "",
    "experience_level": "Intern",
    "current_page": "home",
    "use_voice_mode": False,
    "user_id": "",
    "interview_id": "",
    "interview_question": "",
    "qa_history": list,
    "answer_input": "",
    "pending_answer_text": None,
    "pending_inline_audio": (lambda: b""),
    "evaluation_feedback": "",
    "feedback_audio_bytes": (lambda: b""),
    "feedback_audio_source": "",
    "feedback_audio_nonce": 0,
    "question_audio_bytes": (lambda: b""),
    "question_audio_source": "",
    "question_audio_nonce": 0,
    "last_interview_id": "",
    "alert_message": "",
    "alert_level": "info",
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        if callable(default):
            st.session_state[key] = default()
        elif isinstance(default, list):
            st.session_state[key] = list(default)
        else:
            st.session_state[key] = default


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


def reset_to_home() -> None:
    for key, default in DEFAULT_STATE.items():
        if callable(default):
            st.session_state[key] = default()
        elif isinstance(default, list):
            st.session_state[key] = list(default)
        else:
            st.session_state[key] = default
    _request_rerun()


def render_page_header(title: str, subtitle: str) -> None:
    st.header(title)
    st.caption(subtitle)


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
            return response.json().get("transcript", "").strip()
        except requests.RequestException as exc:
            st.error(f"Failed to transcribe audio: {exc}")
            return ""


def transcribe_inline_audio(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    payload = audio_bytes or b""
    if not payload:
        return ""

    with st.spinner("Transcribing recording..."):
        try:
            files = {
                "file": (
                    "inline_recording.wav",
                    payload,
                    "audio/wav",
                )
            }
            response = requests.post(
                f"{BACKEND_URL}/voice-to-text",
                files=files,
                data={"sample_rate": sample_rate},
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("transcript", "").strip()
        except requests.RequestException as exc:
            st.error(f"Unable to transcribe recording: {exc}")
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


def render_hidden_audio_player(
    audio_bytes: bytes,
    *,
    element_id: str,
    refresh_token: int,
    playback_rate: float,
) -> None:
    if not audio_bytes:
        return

    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    dom_id = f"{element_id}-{refresh_token}"
    components.html(
        f"""
        <audio id="{dom_id}" src="data:audio/mp3;base64,{encoded}" style="display:none;"></audio>
        <script>
            const audioEl = document.getElementById("{dom_id}");
            if (audioEl) {{
                const attemptPlay = () => {{
                    audioEl.playbackRate = {playback_rate};
                    const promise = audioEl.play();
                    if (promise !== undefined) {{
                        promise.catch(() => {{
                            audioEl.style.display = 'block';
                            audioEl.controls = true;
                        }});
                    }}
                }};
                audioEl.addEventListener('canplay', attemptPlay, {{ once: true }});
            }}
        </script>
        """,
        height=0,
    )


def replay_question_audio() -> None:
    st.session_state["question_audio_nonce"] = st.session_state.get("question_audio_nonce", 0) + 1
    _request_rerun()


def replay_feedback_audio() -> None:
    st.session_state["feedback_audio_nonce"] = st.session_state.get("feedback_audio_nonce", 0) + 1
    _request_rerun()


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
        st.session_state["question_audio_nonce"] = st.session_state.get("question_audio_nonce", 0) + 1


def ensure_feedback_audio(feedback: str) -> None:
    summary = (feedback or "").strip()
    if not summary or not st.session_state.get("use_voice_mode"):
        return
    if st.session_state.get("feedback_audio_source") == summary:
        return
    audio_bytes = synthesize_text_to_voice(summary, state_key="feedback_audio_bytes")
    if audio_bytes:
        st.session_state["feedback_audio_source"] = summary
        st.session_state["feedback_audio_nonce"] = st.session_state.get("feedback_audio_nonce", 0) + 1


def render_chat_history(history, pending_question: str) -> None:
    conversation_rendered = False
    for turn in history:
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()
        if question:
            with st.chat_message("assistant"):
                st.write(question)
            conversation_rendered = True
        if answer:
            with st.chat_message("user"):
                st.write(answer)
            conversation_rendered = True

    pending_question = (pending_question or "").strip()
    if pending_question:
        last_question = (history[-1].get("question", "") if history else "").strip()
        if pending_question != last_question:
            with st.chat_message("assistant"):
                st.write(pending_question)
            conversation_rendered = True

    if not conversation_rendered:
        st.info("No messages yet. Start the interview to receive questions.")


def render_home() -> None:
    with st.container():
        st.caption("🎯 Your agentic mock interviewer")
        st.header("Interview Practice Partner")
        st.write(
            "Run lifelike mock interviews with dynamic follow-ups, voice-ready flows, and actionable feedback insights."
        )
        st.write("Choose roles, test scenarios, and refine every response with confidence.")

    with st.container():
        step_cols = st.columns(3)
        step_cols[0].metric(label="Step 1", value="Profile")
        step_cols[1].metric(label="Step 2", value="Domain")
        step_cols[2].metric(label="Step 3", value="Interview")

    if st.button("Get Started", use_container_width=True):
        go_to("user_info")


def render_user_info() -> None:
    nav_cols = st.columns([1, 1, 6])
    with nav_cols[0]:
        st.button("← Back", on_click=go_to, args=("home",), key="back_home")
    with nav_cols[1]:
        st.button("🏠 Go Home", on_click=reset_to_home, key="home_from_profile")

    render_page_header("Tell us about you", "We’ll personalize prompts and follow-ups based on your profile.")

    with st.container():
        name = st.text_input(
            "Full Name",
            value=st.session_state["candidate_name"],
            placeholder="Your Name",
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
    nav_cols = st.columns([1, 1, 6])
    with nav_cols[0]:
        st.button("← Back", on_click=go_to, args=("user_info",), key="back_user")
    with nav_cols[1]:
        st.button("🏠 Go Home", on_click=reset_to_home, key="home_from_domain")

    render_page_header("Pick your practice domain", "Preview upcoming interview packs and plan your practice journey.")

    with st.container():
        domain_options = [
            "Agentic AI",
            "Sales",
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
    nav_cols = st.columns([1, 1, 6])
    with nav_cols[0]:
        st.button("← Back", on_click=go_to, args=("domain",), key="back_to_domain")
    with nav_cols[1]:
        st.button("🏠 Go Home", on_click=reset_to_home, key="home_from_interview")

    render_page_header(
        "Interview Playground",
        "Answer in a chat-style flow, then let the evaluator summarize your run.",
    )

    summary_role = _resolve_domain_label()
    with st.container():
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

    with st.container():
        st.subheader("Chat history")
        render_chat_history(history, current_question if interview_active else "")

        if interview_active and st.session_state.get("question_audio_bytes"):
            if voice_mode:
                render_hidden_audio_player(
                    st.session_state["question_audio_bytes"],
                    element_id="question-audio",
                    refresh_token=st.session_state.get("question_audio_nonce", 0),
                    playback_rate=1.5,
                )
                if st.button("Replay question audio", key="replay_question_btn"):
                    replay_question_audio()
            else:
                st.audio(st.session_state["question_audio_bytes"], format="audio/mp3")

    if interview_active:
        with st.container():
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

            if voice_mode:
                st.caption("🎙️ Voice reply (tap to record)")
                st.caption("Inline recorder")
                recorded_audio = audio_recorder(
                    text="Tap to record / stop",
                    recording_color="#22c55e",
                    neutral_color="#1e293b",
                    icon_name="microphone",
                    sample_rate=16000,
                    pause_threshold=1.2,
                )
                if recorded_audio:
                    st.session_state["pending_inline_audio"] = recorded_audio

                inline_audio = st.session_state.get("pending_inline_audio", b"")
                if inline_audio:
                    st.info("Recording ready. Press Send to auto-transcribe and submit.")
                    if st.button("Discard recording", key="discard_inline_btn"):
                        st.session_state["pending_inline_audio"] = b""
                        inline_audio = b""

            send_col, finish_col = st.columns([3, 2])
            send_clicked = False
            with send_col:
                send_clicked = st.button("Send", use_container_width=True, key="send_answer_btn")
            with finish_col:
                if st.button("Finish", use_container_width=True, key="finish_interview_btn"):
                    complete_mock_interview()

            if send_clicked:
                answer_text = st.session_state.get("answer_input", "")
                inline_audio = st.session_state.get("pending_inline_audio", b"") if voice_mode else b""
                can_submit = True

                if voice_mode and inline_audio:
                    transcript = transcribe_inline_audio(inline_audio)
                    if transcript:
                        answer_text = transcript
                        st.session_state["pending_inline_audio"] = b""
                        set_alert("Recording transcribed. Sending your answer.", "success")
                    else:
                        set_alert("Unable to transcribe the recording. Please retry or type your answer.", "error")
                        can_submit = False

                if can_submit:
                    submit_answer_to_mock_interview(answer_text)

    else:
        with st.container():
            st.info("No active session yet. Start when you're ready to practice.")
            if not st.session_state.get("user_id"):
                st.warning("Please complete profile + domain setup first.")
            if st.button("Start interview", use_container_width=True, key="start_interview_btn"):
                start_mock_interview()

    feedback = (st.session_state.get("evaluation_feedback") or "").strip()
    if feedback:
        with st.container():
            st.subheader("Evaluator feedback")
            st.write(feedback)
            if voice_mode:
                ensure_feedback_audio(feedback)
            else:
                if st.button("Convert feedback to audio", key="convert_feedback_audio"):
                    synthesize_text_to_voice(feedback, state_key="feedback_audio_bytes")
                    st.session_state["feedback_audio_source"] = feedback
            if st.session_state.get("feedback_audio_bytes"):
                if voice_mode:
                    render_hidden_audio_player(
                        st.session_state["feedback_audio_bytes"],
                        element_id="feedback-audio",
                        refresh_token=st.session_state.get("feedback_audio_nonce", 0),
                        playback_rate=1.2,
                    )
                    if st.button("Replay feedback audio", key="replay_feedback_btn"):
                        replay_feedback_audio()
                else:
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
