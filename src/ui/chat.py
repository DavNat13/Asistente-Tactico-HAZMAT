import streamlit as st
from src.retrieval.retriever import retriever
from src.generate.generator import generator
from src.ui.components.chat_bubble import render_assistant_bubble
from src.ui.components.source_card import render_sources_section
from src.ui.components.error_display import render_error, render_empty_context
from src.ui.components.loading_states import render_skeleton


def render_history():
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.history:
            role = message["role"]
            content = message["content"]
            sources = message.get("sources", [])
            if role == "assistant":
                render_assistant_bubble(content, sources)
            else:
                with st.chat_message("user"):
                    st.markdown(content)
    return chat_container


def handle_query(chat_container):
    if query := st.chat_input("Consulte el manual GRE..."):
        session_id = st.session_state.get("session_id")
        thread_id = st.session_state.get("thread_id")
        manager = st.session_state.get("session_manager")

        st.session_state.history.append(
            {"role": "user", "content": query}
        )
        if manager and session_id and thread_id:
            manager.add_user_message(session_id, thread_id, query)

        with chat_container:
            with st.chat_message("user"):
                st.markdown(query)
            with st.chat_message("assistant"):
                response = _process_query(query)
                if response["answer"]:
                    st.markdown(response["answer"])
                    _render_response_sources(response)
                else:
                    render_empty_context()
                    response["answer"] = ""

        if manager and session_id and thread_id:
            manager.add_assistant_message(
                session_id, thread_id, response["answer"],
                sources=response.get("sources", []),
                context_used=response.get("context_used", 0),
            )
        _save_to_history(response)


def _process_query(query):
    with st.spinner("Buscando en el manual GRE..."):
        context_chunks = retriever.retrieve(query)
        response = generator.generate(
            query=query,
            context_chunks=context_chunks,
            history=st.session_state.history[:-1],
        )
    return response


def _render_response_sources(response):
    if response.get("sources"):
        render_sources_section(response["sources"])


def _save_to_history(response):
    st.session_state.history.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response.get("sources", []),
    })
