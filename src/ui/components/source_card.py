import streamlit as st


def render_source_card(source):
    score = source.get("score", 0)
    page = source.get("page", 0)
    doc = source.get("source", "GRE")
    intensity = "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
    html = (
        f'<div class="source-card source-card--{intensity}">'
        f'<span class="source-page">Pagina {page}</span>'
        f'<span class="source-score">{score:.2f}</span>'
        f'<span class="source-doc text-xs text-muted">{doc}</span>'
        f"</div>"
    )
    return html


def render_sources_section(sources):
    if not sources:
        return
    with st.expander("Fuentes consultadas"):
        for s in sources:
            st.markdown(render_source_card(s), unsafe_allow_html=True)
