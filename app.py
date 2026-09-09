import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ui.styles import load_css_files, init_session_state
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_history, handle_query

st.set_page_config(
    page_title="Asistente Táctico HAZMAT",
    page_icon="🔥",
    layout="wide"
)

load_css_files()
init_session_state()
render_sidebar()

st.title("Asistente Táctico HAZMAT")
st.caption("Bomberos de Chile - Guía de Respuesta en Emergencias")

chat_container = render_history()
handle_query(chat_container)
