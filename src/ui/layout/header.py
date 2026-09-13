import streamlit as st
from src.utils.constants import APP_NAME, APP_SUBTITLE


def render_header():
    logo_path = "data/bomberos-de-chile-logo.png"
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image(logo_path, width=64)
    with col2:
        st.markdown(f"## {APP_NAME}")
        st.caption(APP_SUBTITLE)
    with col3:
        st.markdown(
            '<div class="status-label">'
            '<span class="status-dot online"></span>'
            '<span class="text-sm">En linea</span>'
            '</div>',
            unsafe_allow_html=True,
        )
