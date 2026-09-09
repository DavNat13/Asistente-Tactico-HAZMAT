import streamlit as st
import os


def load_css_files():
    styles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "styles")
    css_files = [
        "layout.css",
        "buttons.css",
        "chat.css",
        "typography.css",
        "tabs.css",
        "components.css"
    ]
    combined_css = ""
    for css_file in css_files:
        css_path = os.path.join(styles_dir, css_file)
        if os.path.exists(css_path):
            with open(css_path) as f:
                combined_css += f.read() + "\n"
    st.markdown(f"<style>{combined_css}</style>", unsafe_allow_html=True)


def init_session_state():
    import uuid
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "history" not in st.session_state:
        st.session_state.history = []
