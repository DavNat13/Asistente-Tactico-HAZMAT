import streamlit as st
from src.retrieval.retriever import retriever
from src.generate.generator import generator


def render_source_card(source):
    return (
        f'<div class="source-card">'
        f'Página {source["page"]} | Score: {source["score"]:.2f}'
        f'</div>'
    )


def render_history():
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("Fuentes consultadas"):
                        for source in message["sources"]:
                            st.markdown(render_source_card(source), unsafe_allow_html=True)
    return chat_container


def handle_query(chat_container):
    if query := st.chat_input("Consulte el manual GRE..."):
        st.session_state.history.append({"role": "user", "content": query})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(query)

            with st.chat_message("assistant"):
                response = _process_query(query)
                st.markdown(response["answer"])
                _render_response_sources(response)

        _save_to_history(response)


def _process_query(query):
    with st.spinner("Buscando en el manual GRE..."):
        context_chunks = retriever.retrieve(query)
        response = generator.generate(
            query=query,
            context_chunks=context_chunks,
            history=st.session_state.history[:-1]
        )
    return response


def _render_response_sources(response):
    if response["sources"]:
        with st.expander("Fuentes consultadas"):
            for source in response["sources"]:
                st.markdown(render_source_card(source), unsafe_allow_html=True)


def _save_to_history(response):
    st.session_state.history.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response["sources"]
    })
