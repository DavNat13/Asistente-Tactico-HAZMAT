"""Pantalla de acceso: panel de marca + tarjeta con pestañas (Entrar / Registrarme) o el paso pendiente."""

from __future__ import annotations

import streamlit as st

from src.ui.auth_common import flow, show_notice
from src.ui.auth_forms import login_form
from src.ui.auth_register import register_form
from src.ui.auth_reset import reset_step
from src.ui.auth_steps import email_step, privacy_step, verify_step
from src.ui.icons import icon
from src.ui.privacy_dialog import legal_line
from src.ui.theme import mark

FEATURES = (
    (
        "book",
        "Respuestas con fuente",
        "Cada dato cita la página de la GRE 2024 o del Manual ABC-V.",
    ),
    (
        "zap",
        "Del dato al plan de respuesta",
        "Desde un N° UN hasta un plan completo para el incidente.",
    ),
    (
        "shield",
        "Privado y seguro",
        "Tus conversaciones son solo tuyas. Los datos personales se ocultan.",
    ),
)
STEPS = {
    "verify": verify_step,
    "email": email_step,
    "privacy": privacy_step,
    "reset": reset_step,
}


def _brand_panel() -> None:
    features = "".join(
        f'<div class="hz-feature"><i>{icon(ic)}</i><div><b>{t}</b><span>{d}</span></div></div>'
        for ic, t, d in FEATURES
    )
    st.html(
        '<div class="hz-auth">'
        f'<div><div class="hz-auth-brand">{mark()}<b>Asistente HAZMAT</b></div>'
        "<h2>Decisiones más seguras ante materiales peligrosos.</h2>"
        '<p class="lead">Asistente de IA para Bomberos de Chile basado en la Guía de Respuesta '
        "en Emergencias 2024.</p>"
        f"{features}</div>"
        "<small>GRE 2024 · Manual ABC-V · Uso exclusivo de personal de emergencias</small></div>"
    )


def _tabs() -> None:
    mode = st.segmented_control(
        "Acceso",
        ["Entrar", "Registrarme"],
        format_func=lambda o: (
            f":material/login: {o}" if o == "Entrar" else f":material/person_add: {o}"
        ),
        default="Entrar",
        required=True,
        key="auth_mode",
        label_visibility="collapsed",
        width="stretch",
    )
    if mode == "Registrarme":
        register_form()
    else:
        login_form()


def render_auth() -> None:
    left, right = st.columns(2, gap="large", vertical_alignment="center")
    with left:
        _brand_panel()
    with right, st.container(key="auth_panel", border=False):
        show_notice()
        current = flow()
        step = STEPS.get(current["step"]) if current else None
        if step:
            step(current)
        else:
            _tabs()
        legal_line()
