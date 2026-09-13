import streamlit as st


def render_typing_indicator():
    html = (
        '<div class="typing-indicator">'
        "<span></span><span></span><span></span>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_skeleton(num_lines=3):
    lines = "".join(
        f'<div class="skeleton skeleton-text"></div>'
        for _ in range(num_lines)
    )
    st.markdown(f'<div class="skeleton-wrapper">{lines}</div>',
                unsafe_allow_html=True)


def render_searching_spinner():
    with st.spinner("Buscando en el manual GRE..."):
        return True
