import os

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
}

for key, value in DEFAULT_STATE.items():
    st.session_state.setdefault(key, value)


def go_to(page: str) -> None:
    st.session_state["current_page"] = page
    rerun = getattr(st, "rerun", getattr(st, "experimental_rerun", None))
    if rerun:
        rerun()


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


def synthesize_text_to_voice(text: str) -> bytes:
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
            st.session_state["tts_audio_bytes"] = response.content
            return response.content
        except requests.RequestException as exc:
            st.error(f"Failed to generate voice: {exc}")
            return b""


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
        go_to("domain")


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
        st.session_state["selected_domain_choice"] = domain_choice
        st.session_state["custom_domain"] = custom_role
        st.session_state["experience_level"] = experience_choice
        summary_role = custom_role if domain_choice == "Other" and custom_role else domain_choice
        st.success(f"Saved preferences for {summary_role}. Conversational flow coming soon.")

    st.divider()
    st.subheader("Voice mode (beta)")
    st.caption("Convert between spoken and text responses to rehearse hands-free interviews.")

    voice_col, tts_col = st.columns(2)

    with voice_col:
        st.markdown("**Speech → Text**")
        voice_upload = st.file_uploader(
            "Upload an audio note",
            type=["mp3", "wav", "m4a", "webm"],
            key="voice_note_uploader",
        )
        if st.button("Transcribe voice", use_container_width=True, key="transcribe_voice"):
            if voice_upload is None:
                st.warning("Please upload an audio file first.")
            else:
                transcript = transcribe_voice_file(voice_upload)
                if transcript:
                    st.success("Voice captured.")
        if st.session_state.get("voice_transcript"):
            st.text_area(
                "Recognized speech",
                value=st.session_state["voice_transcript"],
                height=160,
                key="voice_transcript_display",
                disabled=True,
            )

    with tts_col:
        st.markdown("**Text → Speech**")
        tts_text = st.text_area(
            "Message to speak",
            value=st.session_state.get("tts_text", ""),
            height=160,
            key="tts_text_area",
        )
        st.session_state["tts_text"] = tts_text
        if st.button("Speak text", use_container_width=True, key="speak_text"):
            if not tts_text.strip():
                st.warning("Enter some text to convert to speech.")
            else:
                audio_bytes = synthesize_text_to_voice(tts_text)
                if audio_bytes:
                    st.success("Generated voice track.")
        if st.session_state.get("tts_audio_bytes"):
            st.audio(st.session_state["tts_audio_bytes"], format="audio/mp3")


page = st.session_state["current_page"]

if page == "home":
    render_home()
elif page == "user_info":
    render_user_info()
else:
    render_domain_selection()
