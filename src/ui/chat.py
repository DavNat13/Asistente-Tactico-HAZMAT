# chat.py — Orquestación UI del chat (status + streaming vía chat_helpers)
import streamlit as st

from src.ui.chat_helpers import drain_stream, finalize_status, process_query
from src.ui.components.chat_bubble import render_assistant_bubble
from src.ui.components.error_display import render_empty_context
from src.ui.components.source_card import render_sources_section
from src.ui.renderers.response_formatter import format_response


def render_history():
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.history:
            if message["role"] == "assistant":
                render_assistant_bubble(message["content"], message.get("sources", []))
            else:
                with st.chat_message("user"):
                    st.markdown(message["content"])
    return chat_container


def handle_query(chat_container):
    if query := st.chat_input("Consulte el manual GRE..."):
        session_id = st.session_state.get("session_id")
        thread_id = st.session_state.get("thread_id")
        manager = st.session_state.get("session_manager")

        st.session_state.history.append({"role": "user", "content": query})
        if manager and session_id and thread_id:
            manager.add_user_message(session_id, thread_id, query)

        with chat_container:
            with st.chat_message("user"):
                st.markdown(query)
            with st.chat_message("assistant"):
                # Sin `with`: el estado no se auto-cierra; lo cerramos con update()
                status = st.status("Analizando consulta...", expanded=True)
                result = process_query(query, status)

                if result.get("stream") is not None:
                    response = drain_stream(result, status)
                else:
                    response = result["response"]
                    finalize_status(status, response)

                if response["answer"]:
                    if result.get("stream") is None:
                        st.markdown(format_response(response["answer"]),
                                    unsafe_allow_html=True)
                    _render_response_sources(response)
                else:
                    render_empty_context()
                    response["answer"] = ""

        if manager and session_id and thread_id:
            manager.add_assistant_message(
                session_id,
                thread_id,
                response["answer"],
                sources=response.get("sources", []),
                context_used=response.get("context_used", 0),
            )
        _save_to_history(response)


def _render_response_sources(response):
    if response.get("sources"):
        render_sources_section(response["sources"])


def _save_to_history(response):
    st.session_state.history.append(
        {
            "role": "assistant",
            "content": response["answer"],
            "sources": response.get("sources", []),
        }
    )
