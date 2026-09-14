# empty_state.py — Estado vacío de bienvenida
"""Muestra el estado inicial cuando no hay mensajes."""
import streamlit as st


def render_empty_state():
    """Renderiza el estado vacío con diseño limpio."""
    st.markdown(
        '<div style="text-align:center;padding:8rem 1.5rem 0;max-width:520px;margin:0 auto">'
        '<h2 style="color:#F5F2E9;font-size:1.5rem;font-weight:700;'
        'margin:0 0 0.5rem 0">Bienvenido</h2>'
        '<p style="color:rgba(245,242,233,0.6);font-size:0.9rem;line-height:1.6;'
        'margin:0;max-width:400px;margin-left:auto;margin-right:auto">'
        'Asistente táctico para consultas sobre el Manual GRE y '
        'protocolos de emergencias HAZMAT.</p></div>',
        unsafe_allow_html=True,
    )
