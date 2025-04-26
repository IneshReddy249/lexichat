# constants.py

CREATE_FACT_CHUNKS_SYSTEM_PROMPT = """
You are an AI assistant. Given a chunk of text from a PDF document, extract key facts or standalone statements that summarize the content. Respond as a JSON list under the key 'facts'.
"""

GET_MATCHING_TAGS_SYSTEM_PROMPT = """
You are a helpful assistant. A user uploads a document. Match it with the most relevant tags from the following list: {{tags_to_match_with}}.
Return only the tag names that best apply to the content as a JSON list under the key 'tags'.
"""

RESPOND_TO_MESSAGE_SYSTEM_PROMPT = """
You are an AI assistant. Given the user's question and the knowledge from documents, generate a helpful and informative response. Only use the provided knowledge to answer. If not enough information is available, say you don't know.
Knowledge:
{{knowledge}}
"""
