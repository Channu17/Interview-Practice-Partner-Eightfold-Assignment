import streamlit as st

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
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_STATE = {
    "candidate_name": "",
    "resume_option": "without",
    "resume_file_name": "",
    "selected_domain_choice": "Sales",
    "custom_domain": "",
    "experience_level": "Intern",
    "current_page": "home",
}

for key, value in DEFAULT_STATE.items():
    st.session_state.setdefault(key, value)


def go_to(page: str) -> None:
    st.session_state["current_page"] = page
    rerun = getattr(st, "rerun", getattr(st, "experimental_rerun", None))
    if rerun:
        rerun()


def render_home() -> None:
    st.title("Interview Practice Partner")
    st.subheader("Mock interviews that adapt to you")
    st.write(
        "Get ready for realistic interview drills with role-specific prompts, follow-up questions, and post-call feedback. "
        "Pick a path that fits your goal, test multiple scenarios, and refine your pitch before the real conversation."
    )

    if st.button("Get Started", use_container_width=True):
        go_to("user_info")


def render_user_info() -> None:
    st.button("← Back", on_click=go_to, args=("home",), key="back_home")
    st.title("Tell us about you")

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
        uploaded_file = st.file_uploader("Upload resume", type=["pdf", "docx"])
        if uploaded_file is not None:
            st.session_state["resume_file_name"] = uploaded_file.name
            st.success(f"Captured resume: {uploaded_file.name}")
    else:
        st.session_state["resume_file_name"] = ""

    if st.button("Next", use_container_width=True, key="user_next"):
        go_to("domain")


def render_domain_selection() -> None:
    st.button("← Back", on_click=go_to, args=("user_info",), key="back_user")
    st.title("Pick your practice domain")

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


page = st.session_state["current_page"]

if page == "home":
    render_home()
elif page == "user_info":
    render_user_info()
else:
    render_domain_selection()
