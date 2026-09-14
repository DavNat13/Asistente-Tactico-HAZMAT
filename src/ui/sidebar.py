# sidebar.py — Panel lateral estilo ChatGPT/Gemini
"""Sidebar con conversaciones recientes, exportación modal y tema visual."""
import streamlit as st
from src.utils.constants import APP_NAME, NEW_CHAT_ICON
from src.ui.sidebar_helpers import create_thread, get_manager, get_sid
from src.ui.sidebar_history import render_historial
from src.ui.sidebar_export import render_exportar


def render_sidebar():
    with st.sidebar:
        _inject_css()
        _render_cabecera()
        _render_nuevo_chat()
        render_historial()
        render_exportar()


def _inject_css():
    st.markdown("""<style>
    /* Export button */
    [data-testid="stSidebar"] .stButton>button.key_export {
        background:transparent!important;color:rgba(245,242,233,.5)!important;
        border:1px solid rgba(245,242,233,.08)!important;border-radius:8px!important;
        font-size:12px!important;padding:6px 12px!important;
        transition:all .2s ease!important;width:100%!important;margin:0!important;
        box-shadow:none!important
    }
    [data-testid="stSidebar"] .stButton>button.key_export:hover {
        background:rgba(245,242,233,.06)!important;border-color:rgba(245,242,233,.15)!important;
        color:#F5F2E9!important
    }
    /* Export modal */
    .export-title{color:#F5F2E9;font-size:18px;font-weight:700;margin-bottom:4px;text-align:center}
    .export-subtitle{color:rgba(245,242,233,.5);font-size:13px;margin-bottom:1.5rem;text-align:center}
    .export-options{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
    .export-option{background:#2A2722;border:1px solid #333;border-radius:12px;padding:1.5rem 1rem;text-align:center;transition:all .2s ease}
    .export-option:hover{border-color:#FFB000;transform:translateY(-2px)}
    .export-option-icon{width:40px;height:40px;margin:0 auto 12px;border-radius:10px;display:flex;align-items:center;justify-content:center}
    .export-option-icon.json{background:rgba(255,176,0,.12);color:#FFB000}
    .export-option-icon.md{background:rgba(206,32,41,.12);color:#CE2029}
    .export-option-label{color:#F5F2E9;font-size:14px;font-weight:600;margin-bottom:4px}
    .export-option-desc{color:rgba(245,242,233,.45);font-size:12px;line-height:1.4}
    </style>""", unsafe_allow_html=True)


def _render_cabecera():
    st.markdown(
        f'<div style="padding:.5rem 0 1.25rem;border-bottom:1px solid rgba(245,242,233,.08);'
        f'margin-bottom:.75rem;text-align:center">'
        f'<div style="font-size:16px;font-weight:700;color:#F5F2E9;line-height:1.3">{APP_NAME}</div>'
        f'<div style="font-size:11px;color:#F5F2E9;line-height:1.2;margin-top:4px;opacity:.5">'
        f'Bomberos de Chile - GRE</div></div>',
        unsafe_allow_html=True,
    )


def _render_nuevo_chat():
    if st.button(f"{NEW_CHAT_ICON} Nuevo Chat", use_container_width=True,
                 type="primary", key="sidebar_nuevo"):
        mgr, sid = get_manager(), get_sid()
        if mgr and sid:
            create_thread(mgr, sid)
    st.markdown("")
