# app.py — Punto de entrada del Dashboard RAG HAZMAT
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ui.chat import handle_query, render_history
from src.ui.components.empty_state import render_empty_state
from src.ui.layout.header import render_header
from src.ui.sidebar import render_sidebar
from src.ui.styles import init_session_state, load_css_files
from src.utils.constants import APP_ICON, APP_NAME

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css_files()

# La sesión puede fallar si MongoDB no está disponible.
# El sidebar debe renderizarse SIEMPRE, aunque la sesión falle.
try:
    init_session_state()
except Exception:  # noqa: BLE001
    st.session_state.setdefault("history", [])

render_sidebar()

render_header()

if not st.session_state.get("history"):
    render_empty_state()

chat_container = render_history()
handle_query(chat_container)
