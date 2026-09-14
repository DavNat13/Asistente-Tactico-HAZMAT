import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.session.manager import SessionManager

MATERIAL_SYMBOLS = (
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined'
    ':opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap">'
)

CSS_FILES = [
    "tokens/colors.css",
    "tokens/tokens.css",
    "tokens/typography.css",
    "tokens/spacing.css",
    "tokens/component-tokens.css",
    "base/animations.css",
    "base/animations-extra.css",
    "base/reset.css",
    "base/rules.css",
    "base/rules-typography.css",
    "components/header.css",
    "components/sidebar.css",
    "components/chat.css",
    "components/buttons.css",
    "components/tabs.css",
    "components/sources.css",
    "components/status.css",
    "components/components.css",
    "utilities/utilities.css",
    "utilities/utilities-layout.css",
    "utilities/responsive.css",
    "utilities/accessibility.css",
]


def load_css_files():
    st.markdown(MATERIAL_SYMBOLS, unsafe_allow_html=True)
    styles_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "styles",
    )
    for css_file in CSS_FILES:
        path = os.path.join(styles_dir, css_file)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _init_session(manager):
    if "session_id" not in st.session_state:
        url_params = st.query_params
        if "session_id" in url_params:
            st.session_state.session_id = url_params["session_id"]
        else:
            session = manager.create_session()
            st.session_state.session_id = session.session_id
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None


def _init_session_object(manager):
    if "session" not in st.session_state:
        st.session_state.session = manager.get_or_create_session(
            st.session_state.session_id
        )


def _init_thread(manager):
    if "thread" not in st.session_state:
        thread = manager.get_or_create_thread(
            st.session_state.session_id,
            st.session_state.thread_id,
        )
        st.session_state.thread = thread
        st.session_state.thread_id = thread.thread_id


def _init_history(manager):
    if "history" not in st.session_state:
        messages = manager.get_history(
            st.session_state.session_id,
            st.session_state.thread_id,
        )
        st.session_state.history = [
            {
                "role": m.role,
                "content": m.content,
                "sources": [
                    {"page": s.page, "source": s.source, "score": s.score}
                    for s in m.sources
                ]
                if m.sources
                else [],
            }
            for m in messages
        ]


def init_session_state():
    manager = SessionManager()
    _init_session(manager)
    _init_session_object(manager)
    _init_thread(manager)
    _init_history(manager)
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = manager
