import streamlit as st
from src.utils.constants import APP_NAME, APP_SUBTITLE


def render_header():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"## {APP_NAME}")
        st.caption(APP_SUBTITLE)
    with col2:
        st.markdown(
            '<div class="status-label">'
            '<span class="status-dot online"></span>'
            '<span class="text-sm">En linea</span>'
            '</div>',
            unsafe_allow_html=True,
        )
