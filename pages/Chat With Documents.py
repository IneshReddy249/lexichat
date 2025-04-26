import asyncio
import os
from typing import Literal, Optional, TypedDict, Union

import streamlit as st
from anyio import sleep
from peewee import SQL
from dotenv import load_dotenv
import openai

# Internal imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from constants import RESPOND_TO_MESSAGE_SYSTEM_PROMPT
from db import db, DocumentInformationChunks

# Load env vars and initialize OpenAI client
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit config
st.set_page_config(page_title="Chat With Documents")
st.title("🗣️ Chat With LexiChat Documents")

# Session state for chat messages
class Message(TypedDict):
    role: Union[Literal["user"], Literal["assistant"]]
    content: str
    references: Optional[list[str]]

if "messages" not in st.session_state:
    st.session_state["messages"] = []

def push_message(message: Message):
    st.session_state["messages"].append(message)

async def get_openai_embedding(text: str):
    try:
        response = await openai.Embedding.acreate(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"❌ Embedding failed: {e}")
        return []

async def send_message(input_message: str):
    # Get embedding from OpenAI
    embedding_vector = await get_openai_embedding(input_message)
    if not embedding_vector:
        return

    related_chunks = []

    with db.atomic():
        # Use vector similarity query
        results = DocumentInformationChunks.select().order_by(
            SQL("embedding <-> %s::vector", (embedding_vector,))
        ).limit(5)

        related_chunks = [r.chunk for r in results]

    push_message({
        "role": "user",
        "content": input_message,
        "references": related_chunks
    })

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": RESPOND_TO_MESSAGE_SYSTEM_PROMPT.replace(
                        "{{knowledge}}",
                        "\n".join([f"{i+1}. {chunk}" for i, chunk in enumerate(related_chunks)])
                    )
                },
                *[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state["messages"]
                ]
            ]
        )
        assistant_msg = response.choices[0].message.content
        push_message({
            "role": "assistant",
            "content": assistant_msg,
            "references": None
        })
    except Exception as e:
        st.error(f"❌ Error from OpenAI: {e}")

    st.rerun()

# Render chat history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["references"]:
            with st.expander("References"):
                for ref in message["references"]:
                    st.write(ref)

# Chat input
input_message = st.chat_input("Ask anything about your uploaded documents...")
if input_message:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_message(input_message))
    loop.close()
