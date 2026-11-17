"""Carga de estilos y elementos de marca."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from src.utils.constants import APP_NAME, APP_SHORT, APP_SUBTITLE

_CSS = Path(__file__).resolve().parents[2] / "styles" / "app.css"


@st.cache_resource
def _css() -> str:
    return _CSS.read_text(encoding="utf-8") if _CSS.exists() else ""


def load_css() -> None:
    # CSS propio (archivo local, no contenido del usuario): seguro con unsafe_allow_html
    st.html(f"<style>{_css()}</style>")


def brand(subtitle: str = APP_SUBTITLE) -> None:
    st.html(
        '<div class="hz-brand">'
        f'<div class="hz-mark">{html.escape(APP_SHORT)}</div>'
        f'<div><div class="hz-title">{html.escape(APP_NAME)}</div>'
        f'<div class="hz-sub">{html.escape(subtitle)}</div></div></div>'
    )
