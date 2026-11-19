"""Modal con el aviso de privacidad COMPLETO (docs/AVISO_PRIVACIDAD.md), índice por anclas y descarga.

`st.dialog` no puede abrirse desde dentro de `st.form`: los botones que lo abren van fuera.
"He leído el aviso" marca `privacy_read`, que habilita la casilla de aceptación.
"""

from __future__ import annotations

import html

import streamlit as st

from src.security.privacy import (
    PRIVACY_DATE,
    PRIVACY_VERSION,
    load_notice,
    split_sections,
)
from src.utils.constants import APP_VERSION

READ_KEY = "privacy_read"


def notice_read() -> bool:
    return bool(st.session_state.get(READ_KEY))


@st.dialog("Aviso de privacidad", width="large", icon=":material/shield:")
def privacy_dialog() -> None:
    text = load_notice()
    preamble, sections = split_sections(text)
    st.caption(
        f"Versión {PRIVACY_VERSION} · Vigente desde el {PRIVACY_DATE} · "
        "Borrador: revisión legal pendiente"
    )
    with st.container(key="privacy_body"):
        st.markdown(preamble.split("\n", 1)[1] if "\n" in preamble else preamble)
        st.markdown(
            "**Índice**\n\n"
            + "\n".join(f"- [{title}](#{anchor})" for anchor, title, _ in sections)
        )
        for anchor, title, body in sections:  # ancla explícita: el modal no las genera
            st.html(f'<h3 id="{anchor}" class="hz-notice-h">{html.escape(title)}</h3>')
            st.markdown(body)
    c1, c2 = st.columns(2)
    c1.download_button(
        "Descargar aviso (.md)",
        data=text.encode("utf-8"),
        file_name=f"aviso_privacidad_{PRIVACY_VERSION}.md",
        mime="text/markdown",
        icon=":material/download:",
        on_click="ignore",
        width="stretch",
    )
    if c2.button(
        "He leído el aviso",
        type="primary",
        icon=":material/task_alt:",
        width="stretch",
        key="privacy_read_btn",
    ):
        st.session_state[READ_KEY] = True
        st.rerun()


def legal_line(key: str = "privacy_footer") -> None:
    """Línea corta del pie: escudo + enlace que abre el modal."""
    with st.container(
        key="auth_legal", horizontal=True, vertical_alignment="center", gap="small"
    ):
        st.caption(
            f":material/shield: Datos protegidos · Ley 21.719 · v{APP_VERSION}",
            width="content",
        )
        if st.button("Aviso de privacidad", type="tertiary", key=key):
            privacy_dialog()


def acceptance(key: str) -> bool:
    """Casilla de aceptación (habilitada tras leer el aviso) + texto que abre el modal."""
    read = notice_read()
    c1, c2 = st.columns([0.08, 0.92], vertical_alignment="center", gap="small")
    accepted = c1.checkbox(
        "Acepto el aviso de privacidad",
        key=key,
        disabled=not read,
        label_visibility="collapsed",
        help=None if read else "Abre y lee el aviso para habilitar la casilla",
    )
    if c2.button(
        "Acepto el aviso de privacidad y el uso como herramienta de apoyo",
        type="tertiary",
        key=f"{key}_open",
        wrap=True,
    ):
        privacy_dialog()
    if not read:
        st.caption("Abre el aviso y pulsa «He leído el aviso» para poder aceptarlo.")
    return bool(accepted and read)
