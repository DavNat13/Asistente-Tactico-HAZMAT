"""Carga de estilos y elementos de marca."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from src.ui.icons import icon
from src.utils.constants import APP_NAME, APP_SUBTITLE

_STYLES = Path(__file__).resolve().parents[2] / "styles"
_FILES = (
    "tokens.css",
    "app.css",
    "nav.css",
    "forms.css",
    "sidebar.css",
    "auth.css",
    "dashboard.css",
    "map.css",
)


@st.cache_resource
def _css() -> str:
    return "\n".join(
        (_STYLES / f).read_text(encoding="utf-8")
        for f in _FILES
        if (_STYLES / f).exists()
    )


def load_css() -> None:
    """CSS propio del proyecto (archivo local, no contenido del usuario)."""
    st.html(f"<style>{_css()}</style>")


def mark() -> str:
    return f'<div class="hz-mark">{icon("flame")}</div>'


def sidebar_brand() -> None:
    st.html(
        f'<div class="hz-side-brand">{mark()}<div><b>{html.escape(APP_NAME)}</b>'
        f"<span>{html.escape(APP_SUBTITLE)}</span></div></div>"
    )
