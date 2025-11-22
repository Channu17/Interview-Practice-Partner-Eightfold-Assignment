import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ROLES = [
    "Software Engineer",
    "Sales Associate",
    "Retail Associate",
    "Product Manager",
]
SCENARIOS = [
    "Confused User",
    "Efficient User",
    "Chatty User",
    "Edge Case User",
]

st.set_page_config(page_title="Interview Practice Partner", page_icon="🎤")
st.title("Interview Practice Partner")
st.caption("Stage 1 setup – conversational logic arrives next.")

role = st.selectbox("Choose a role", ROLES)
scenario = st.selectbox("Pick a demo scenario", SCENARIOS)

st.write("Backend connection status:")
if st.button("Ping API"):
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        response.raise_for_status()
        st.success("Backend reachable")
        st.json(response.json())
    except requests.RequestException as exc:
        st.error(f"Backend unreachable: {exc}")

st.info(
    "Voice and agentic flows will plug in after we lock Stage 1 infrastructure."
)
