import streamlit as st
from src.utils.constants import APP_NAME, EXAMPLE_QUERIES


def render_empty_state():
    st.markdown(
        '<div class="animate-fade-in-up" '
        'style="text-align:center; padding:2rem 0;">'
        '<span style="font-size:3rem;">:material/local_fire_department:</span>'
        f"<h2 style='color:var(--text-primary);'>Bienvenido a {APP_NAME}</h2>"
        '<p class="text-secondary" style="max-width:500px; margin:0 auto;">'
        "Realice preguntas sobre el Manual GRE y obtenga "
        "respuestas tacticas para emergencias HAZMAT."
        "</p></div>",
        unsafe_allow_html=True,
    )
    _render_example_queries()


def _render_example_queries():
    cols = st.columns(len(EXAMPLE_QUERIES))
    for i, query in enumerate(EXAMPLE_QUERIES):
        with cols[i]:
            if st.button(query, key=f"example_{i}", use_container_width=True):
                st.session_state["example_query"] = query
                st.rerun()
