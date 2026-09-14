import streamlit as st


def render_error(message, details=None):
    html = (
        '<div class="hazmat-toast error" style="position:relative;">'
        '<span class="text-emergency font-semibold">'
        "Error</span>"
        f"<p>{message}</p>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
    if details:
        with st.expander("Detalles"):
            st.code(details)


def render_empty_context():
    st.warning(
        "No se encontraron documentos relevantes. Intente reformular su consulta."
    )
