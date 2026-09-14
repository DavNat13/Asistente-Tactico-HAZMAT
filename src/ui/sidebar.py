import streamlit as st
from src.retrieval.retriever import retriever
from src.utils.constants import APP_NAME, NEW_CHAT_ICON, APP_ICON
from src.ui.sidebar_helpers import (
    switch_thread, create_thread, reset_session,
    get_manager, get_sid, get_tid,
)


def render_sidebar():
    with st.sidebar:
        _render_branding()
        _render_stats()
        _render_threads()
        _render_export()
        _render_session_info()
        _render_actions()


def _render_branding():
    st.image("data/bomberos-de-chile-logo.png", width=80)
    st.markdown(f"### {APP_ICON} {APP_NAME}")
    st.caption("Bomberos de Chile - GRE")
    st.divider()


def _render_stats():
    stats = retriever.get_collection_stats()
    st.metric("Documentos Indexados", stats["total_chunks"])
    st.divider()


def _render_threads():
    st.subheader("Hilos de Conversacion")
    mgr, sid = get_manager(), get_sid()
    if not (mgr and sid):
        return
    for t in mgr.get_active_threads(sid):
        cur = t.thread_id == st.session_state.get("thread_id")
        if st.button(f"{'*' if cur else ''} {t.title}",
                      key=f"t_{t.thread_id}", use_container_width=True,
                      type="secondary" if cur else "tertiary"):
            if not cur:
                switch_thread(mgr, sid, t.thread_id)
    st.divider()
    if st.button(f"{NEW_CHAT_ICON} Nuevo Hilo", use_container_width=True):
        create_thread(mgr, sid)


def _render_export():
    st.subheader("Exportar Chat")
    mgr, sid, tid = get_manager(), get_sid(), get_tid()
    if not (mgr and sid and tid):
        st.caption("Inicie una conversacion para exportar")
        return
    c1, c2 = st.columns(2)
    with c1:
        d = mgr.export_chat_bytes(sid, tid, "json")
        if d:
            st.download_button("JSON", data=d, file_name=d.name,
                               mime="application/json",
                               use_container_width=True)
    with c2:
        d = mgr.export_chat_bytes(sid, tid, "markdown")
        if d:
            st.download_button("Markdown", data=d, file_name=d.name,
                               mime="text/markdown",
                               use_container_width=True)


def _render_session_info():
    st.subheader("Sesion")
    sid = get_sid()
    if not sid:
        return
    st.caption(f"ID: {sid[:8]}...")
    mgr = get_manager()
    if mgr:
        s = mgr.get_session_stats(sid)
        if s:
            st.caption(f"Hilos: {s.get('thread_count', 0)}")
            st.caption(f"Mensajes: {s.get('total_messages', 0)}")


def _render_actions():
    st.divider()
    if st.button("Nueva Sesion Completa", use_container_width=True):
        reset_session()
