# pages/Manage Tags.py

import streamlit as st

# --- Fix for relative imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Project imports
from db import Tags

# --- Streamlit Page Setup
st.set_page_config(page_title="Manage Tags")
st.title("🏷️ Manage LexiChat Tags")

# --- Helper: Delete Tag
def delete_tag(tag_id: int):
    Tags.delete().where(Tags.id == tag_id).execute()

# --- Add Tag Dialog
@st.dialog("Add New Tag")
def add_tag_dialog_open():
    new_tag = st.text_input("Enter New Tag Name:")
    if new_tag:
        if st.button("✅ Add Tag", key="confirm-add-tag"):
            Tags.create(name=new_tag)
            st.success(f"Tag '{new_tag}' added successfully!")
            st.rerun()

# --- Add Tag Button
st.button("➕ Add Tag", key="open-add-tag-dialog", on_click=add_tag_dialog_open)

# --- Display Existing Tags
tags = Tags.select()

if tags:
    for tag in tags:
        with st.container(border=True):
            tag_col, spacer_col, delete_col = st.columns([3, 2, 1])

            with tag_col:
                st.write(f"**{tag.name}**")

            with spacer_col:
                pass  # Just spacing

            with delete_col:
                if st.button("🗑 Delete", key=f"delete-tag-{tag.id}"):
                    delete_tag(tag.id)
                    st.success(f"Tag '{tag.name}' deleted successfully!")
                    st.rerun()
else:
    st.info("No tags created yet. Please create one!")
