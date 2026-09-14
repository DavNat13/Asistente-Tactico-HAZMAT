# header.py — Cabecera mínima
"""Oculta decoraciones del header nativo de Streamlit."""
import streamlit as st


def render_header():
    """Oculta Deploy, menú hamburguesa y status widget."""
    st.markdown(
        '<style>'
        '[data-testid="stAppDeployButton"],'
        '[data-testid="stMainMenu"],'
        '[data-testid="stStatusWidget"],'
        '[data-testid="stToolbarActions"]{display:none!important}'
        'header[data-testid="stHeader"]{background:transparent!important;border:none!important;height:0!important;min-height:0!important}'
        '[data-testid="stMain"]{padding-top:0!important}'
        '[data-testid="stMainBlockContainer"]{padding-top:0!important;margin-top:0!important}'
        '</style>',
        unsafe_allow_html=True,
    )
