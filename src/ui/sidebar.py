import streamlit as st
import uuid
from src.retrieval.retriever import retriever


def render_sidebar():
    with st.sidebar:
        st.header("Panel de Control")
        st.divider()

        stats = retriever.get_collection_stats()
        st.metric("Documentos Indexados", stats["total_chunks"])

        st.divider()

        if st.button("Nueva Consulta"):
            st.session_state.history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

        st.divider()
        st.caption(f"Sesión: {st.session_state.session_id[:8]}...")
