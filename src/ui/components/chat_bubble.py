import streamlit as st
from src.ui.renderers.response_formatter import format_response


def render_user_bubble(content):
    with st.chat_message("user"):
        st.markdown(content)


def render_assistant_bubble(content, sources=None):
    formatted = format_response(content)
    with st.chat_message("assistant"):
        st.markdown(formatted, unsafe_allow_html=True)
        if sources:
            _render_sources(sources)


def _render_sources(sources):
    with st.expander("Fuentes consultadas"):
        for s in sources:
            score = s.get("score", 0)
            page = s.get("page", 0)
            color = "var(--color-accent-300)" if score >= 0.7 else "var(--text-muted)"
            html = (
                f'<div class="source-card">'
                f'<span class="source-page" style="color:{color}">'
                f'Pagina {page}</span>'
                f' <span class="source-score">'
                f'Score: {score:.2f}</span></div>'
            )
            st.markdown(html, unsafe_allow_html=True)
