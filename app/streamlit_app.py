import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface

st.set_page_config(
    page_title="RAG - Локальная файловая система",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("styles.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📚 RAG - Локальная файловая система")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

display_sidebar()

display_chat_interface()