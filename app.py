"""Asistente HAZMAT — punto de entrada Streamlit.

Navegación por rol: `operador` ve el chat; `admin` además ve el dashboard de observabilidad.
"""

import logging
import os
import sys
import threading

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import settings
from src.ui import state
from src.ui.auth_view import render_auth
from src.ui.theme import load_css
from src.utils.constants import APP_ICON, APP_NAME

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")
load_css()


@st.cache_resource(show_spinner=False)
def _warmup() -> bool:
    """Carga el modelo de embeddings en segundo plano al iniciar (evita ~30 s en la 1.ª consulta)."""
    from src.ingesta.processor import get_embeddings

    threading.Thread(target=get_embeddings, daemon=True).start()
    return True


_warmup()

if settings.AUTH_ENABLED and not state.user():
    render_auth()
    st.stop()
if not settings.AUTH_ENABLED and not state.user():
    st.session_state.user = {"username": "local", "name": "Modo local", "role": "admin"}

from src.ui.pages import available

st.navigation(available(), position="top").run()
