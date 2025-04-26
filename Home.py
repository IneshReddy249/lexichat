# Home.py
import streamlit as st

st.set_page_config(
    page_title="LexiChat Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Welcome to LexiChatBot")
st.markdown("""
LexiChatBot is your GenAI-powered assistant to interact with documents.
Use the sidebar to:
- 🗣️ Chat with uploaded documents
- 📄 Upload and manage documents
- 🏷️ Add or remove tags for classification
""")

st.info("Select a feature from the left sidebar to get started!")
