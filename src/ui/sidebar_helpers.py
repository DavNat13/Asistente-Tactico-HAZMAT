import streamlit as st


def switch_thread(mgr, sid, tid):
    t = mgr.get_thread(sid, tid)
    if not t:
        return
    st.session_state.thread_id = tid
    st.session_state.thread = t
    msgs = mgr.get_history(sid, tid)
    st.session_state.history = [
        {"role": m.role, "content": m.content,
         "sources": [{"page": s.page, "source": s.source,
                      "score": s.score} for s in m.sources]
         if m.sources else []}
        for m in msgs
    ]
    st.rerun()


def create_thread(mgr, sid):
    t = mgr.create_thread(sid)
    st.session_state.thread_id = t.thread_id
    st.session_state.thread = t
    st.session_state.history = []
    st.rerun()


def reset_session():
    mgr = st.session_state.get("session_manager")
    if mgr:
        mgr.close()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def get_manager():
    return st.session_state.get("session_manager")


def get_sid():
    return st.session_state.get("session_id")


def get_tid():
    return st.session_state.get("thread_id")
