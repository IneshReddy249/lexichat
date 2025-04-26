# pages/Manage Documents.py

import asyncio
import os
from io import BytesIO
from itertools import chain

import streamlit as st
import openai
from dotenv import load_dotenv
from peewee import SQL, JOIN, NodeList
import pdftotext
from pydantic import BaseModel
from anyio import sleep

# --- Internal imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from constants import CREATE_FACT_CHUNKS_SYSTEM_PROMPT, GET_MATCHING_TAGS_SYSTEM_PROMPT
from db import db, Documents, Tags, DocumentTags, DocumentInformationChunks
from utils import find

# ------------------------- Load environment -------------------------
load_dotenv()

# ------------------------- Streamlit UI -------------------------
st.set_page_config(page_title="Manage Documents")
st.title("📄 Manage LexiChat Documents")
openai.api_key = os.getenv("OPENAI_API_KEY")


IDEAL_CHUNK_LENGTH = 4000

# ------------------------- Models -------------------------

class GeneratedDocumentInformationChunks(BaseModel):
    facts: list[str]

class GeneratedMatchingTags(BaseModel):
    tags: list[str]

# ------------------------- Helper Functions -------------------------

async def get_openai_embedding(text: str) -> list[float]:
    """Generate OpenAI Embedding for given text."""
    response = await openai.Embedding.acreate(
        model="text-embedding-ada-002",
        input=text
    )
    return response["data"][0]["embedding"]

async def generate_chunks(index: int, text_chunk: str):
    retries = 0
    while retries <= 5:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": CREATE_FACT_CHUNKS_SYSTEM_PROMPT},
                    {"role": "user", "content": text_chunk}
                ],
                temperature=0.2
            )
            facts_obj = GeneratedDocumentInformationChunks.model_validate_json(response["choices"][0]["message"]["content"])
            return facts_obj.facts
        except Exception as e:
            retries += 1
            print(f"❌ Retry {retries} on chunk {index}: {e}")
            await sleep(2)
    raise Exception(f"Chunk {index} failed after retries.")

async def get_matching_tags(pdf_text: str):
    retries = 0
    tags_query = Tags.select()
    tag_names = [tag.name.lower() for tag in tags_query]

    if not tag_names:
        return []

    while retries <= 5:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": GET_MATCHING_TAGS_SYSTEM_PROMPT.replace("{{tags_to_match_with}}", str(tag_names))},
                    {"role": "user", "content": pdf_text[:5000]}
                ],
                temperature=0.2
            )
            matched = GeneratedMatchingTags.model_validate_json(response["choices"][0]["message"]["content"])
            all_tags = list(tags_query)
            return [tag.id for tag in all_tags if tag.name.lower() in map(str.lower, matched.tags)]
        except Exception as e:
            retries += 1
            print(f"❌ Retry {retries} on tag matching: {e}")
            await sleep(2)
    raise Exception("Tag matching failed.")

def delete_document(document_id: int):
    Documents.delete().where(Documents.id == document_id).execute()

# ------------------------- Upload Logic -------------------------

def upload_document(name: str, pdf_bytes: bytes):
    parsed = pdftotext.PDF(BytesIO(pdf_bytes))
    text = "\n\n".join(parsed)
    chunks = [text[i:i + IDEAL_CHUNK_LENGTH] for i in range(0, len(text), IDEAL_CHUNK_LENGTH)]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Step 1: Generate facts and tags
    facts_batches, matching_tag_ids = loop.run_until_complete(asyncio.gather(
        asyncio.gather(*(generate_chunks(i, chunk) for i, chunk in enumerate(chunks))),
        get_matching_tags(text)
    ))
    facts = list(chain.from_iterable(facts_batches))

    # Step 2: Embed all facts
    embeddings = loop.run_until_complete(
        asyncio.gather(*(get_openai_embedding(fact) for fact in facts))
    )

    with db.atomic():
        # Insert document
        document_id = Documents.insert(name=name).execute()

        # Insert facts + embeddings
        for fact, embedding in zip(facts, embeddings):
            DocumentInformationChunks.create(
                document_id=document_id,
                chunk=fact,
                embedding=embedding
            )

        # Insert matching tags
        if matching_tag_ids:
            DocumentTags.insert_many([
                {"document_id": document_id, "tag_id": tag_id}
                for tag_id in matching_tag_ids
            ]).execute()

    loop.close()

# ------------------------- Streamlit UI -------------------------

@st.dialog("➕ Upload PDF Document")
def show_upload_dialog():
    pdf_file = st.file_uploader("Choose a PDF file", type="pdf")
    if pdf_file and st.button("✅ Upload"):
        upload_document(pdf_file.name, pdf_file.read())
        st.success(f"Document {pdf_file.name} uploaded successfully!")
        st.rerun()

st.button("➕ Upload New Document", on_click=show_upload_dialog)

documents = Documents.select(
    Documents.id,
    Documents.name,
    NodeList([
        SQL('array_remove(array_agg('), Tags.name, SQL('), NULL)')
    ]).alias("tags")
).join(DocumentTags, JOIN.LEFT_OUTER).join(Tags, JOIN.LEFT_OUTER).group_by(Documents.id)

if documents:
    for doc in documents:
        with st.container(border=True):
            st.subheader(doc.name)
            if doc.tags:
                st.caption("Tags: " + ", ".join(doc.tags))
            st.button("🗑 Delete", key=f"delete-{doc.id}", on_click=lambda d=doc.id: delete_document(d))
else:
    st.info("No documents found. Please upload a PDF!")
