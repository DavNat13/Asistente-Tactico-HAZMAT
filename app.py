# app.py — Punto de entrada del Dashboard RAG HAZMAT
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ui.styles import load_css_files, init_session_state
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_history, handle_query
from src.ui.layout.header import render_header
from src.ui.components.empty_state import render_empty_state
from src.utils.constants import APP_NAME, APP_ICON

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
except Exception:
    st.session_state.setdefault("history", [])

render_sidebar()

render_header()

if not st.session_state.get("history"):
    render_empty_state()

chat_container = render_history()
handle_query(chat_container)
