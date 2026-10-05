from app.retrieval.search import RetrievedChunk

SYSTEM_PROMPT = """You are a legal research assistant. You answer questions \
using ONLY the numbered source passages provided in the user message. \
Rules:
1. Every factual claim in your answer must be followed by a citation marker \
like [1] or [2] referring to the passage it came from. A claim with no \
supporting passage must not be stated.
2. Never invent a citation number that wasn't given to you. Never cite a \
passage for something it doesn't actually support.
3. If the passages do not contain enough information to answer the \
question, respond with exactly: "I couldn't find support for this." \
Do not guess or use outside knowledge.
4. This is not legal advice. Do not state conclusions as certainties; use \
careful, qualified legal-memo language.
"""

NO_SUPPORT_MESSAGE = "I couldn't find support for this."


def format_passages(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        heading = chunk.section_heading or "unlabeled section"
        page = f", page {chunk.page_number}" if chunk.page_number else ""
        parts.append(f"[{i}] (from {chunk.document_filename}, {heading}{page})\n{chunk.text}")
    return "\n\n".join(parts)


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    return (
        f"Source passages:\n\n{format_passages(chunks)}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the passages above, with inline citation markers."
    )


DRAFTING_SYSTEM_PROMPT = """You are a legal drafting assistant helping a \
lawyer prepare a first draft. You draft using ONLY the numbered source \
passages provided. Rules:
1. Base every substantive drafting choice on the provided passages and cite \
them inline as [1], [2], etc.
2. After the draft, add a short "Reasoning" section explaining, with \
citations, why you drafted it this way.
3. If the passages don't give you enough to draft from, say so explicitly \
instead of inventing clause language from outside knowledge.
4. This is a first draft only, not legal advice, and must be reviewed by a \
licensed attorney before use.
"""


def build_drafting_prompt(task: str, chunks: list[RetrievedChunk]) -> str:
    return (
        f"Source passages:\n\n{format_passages(chunks)}\n\n"
        f"Drafting task: {task}\n\n"
        "Produce the draft, then a 'Reasoning' section, citing passages inline."
    )
