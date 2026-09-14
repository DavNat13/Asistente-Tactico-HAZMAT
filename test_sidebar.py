import streamlit as st

st.set_page_config(
    page_title="Test Sidebar", layout="wide", initial_sidebar_state="expanded"
)

with st.sidebar:
    st.markdown("### Sidebar Test")
    st.markdown("¿Me ves?")
    if st.button("Click me"):
        st.sidebar.success("Funciona!")

st.markdown("### Main Content")
st.markdown("El sidebar debería verse a la izquierda.")
