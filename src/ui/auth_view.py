"""Pantalla de acceso: panel de marca + formularios de inicio de sesión y registro."""

from __future__ import annotations

import streamlit as st

from src.config.settings import settings
from src.ui.auth_forms import login_form, register_form
from src.ui.icons import MUTED, icon
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

PRIVACY = (
    f"{icon('lock', MUTED, 13)}Tus consultas se procesan para responderte. RUT, teléfonos, correos y patentes se "
    "ocultan automáticamente antes de llegar al modelo de IA. El historial se conserva "
    f"{settings.SESSION_TTL_DAYS} días y puedes eliminarlo cuando quieras (Ley 19.628 y Ley 21.719). "
    "Las direcciones del mapa se buscan en OpenStreetMap y las fotos de placas se analizan sin "
    "guardarse. Herramienta de apoyo: no reemplaza al mando del incidente."
)


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


def render_auth() -> None:
    left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
    with left:
        _brand_panel()
    with right, st.container(key="auth_panel", border=False):
        mode = st.segmented_control(
            "Acceso",
            ["Iniciar sesión", "Crear cuenta"],
            format_func=lambda o: (
                f":material/login: {o}"
                if o == "Iniciar sesión"
                else f":material/person_add: {o}"
            ),
            default="Iniciar sesión",
            required=True,
            key="auth_mode",
            label_visibility="collapsed",
        )
        if mode == "Crear cuenta":
            register_form()
        else:
            login_form()
        st.html(f'<p class="hz-legal">{PRIVACY}</p>')
