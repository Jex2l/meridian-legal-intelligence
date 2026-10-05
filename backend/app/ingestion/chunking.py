"""Legal-aware chunking: split by clause/section heading rather than a fixed
token window. Falls back to paragraph grouping when no headings are found
(e.g. a memo with no numbered structure).
"""

import re
from dataclasses import dataclass, field

from app.ingestion.extract import ExtractedDocument

# Headings we recognize, roughly in nesting order (top-level first):
#   ARTICLE I, ARTICLE 1          -> level 0
#   Section 1, SECTION 1.2        -> level 1
#   1. Foo / 1.1 Foo               -> level 1 (numbered clause)
#   (a) Foo / (i) Foo              -> level 2 (lettered/roman sub-clause)
_HEADING_PATTERNS: list[tuple[int, re.Pattern]] = [
    (0, re.compile(r"^\s*ARTICLE\s+[IVXLCDM0-9]+\b.*$", re.IGNORECASE)),
    (1, re.compile(r"^\s*SECTION\s+[0-9]+(\.[0-9]+)*\b.*$", re.IGNORECASE)),
    (1, re.compile(r"^\s*[0-9]+(\.[0-9]+)*[.)]\s+\S.*$")),
    (2, re.compile(r"^\s*\([a-z]{1,3}\)\s+\S.*$")),
    (2, re.compile(r"^\s*\([ivx]{1,4}\)\s+\S.*$", re.IGNORECASE)),
    (0, re.compile(r"^\s*[A-Z][A-Z0-9 ,.'&/-]{4,}$")),  # ALL CAPS heading line
]

_FALLBACK_CHUNK_CHARS = 1200


@dataclass
class RawChunk:
    text: str
    section_heading: str | None
    page_number: int | None
    level: int
    parent_index: int | None = None  # index into the returned list, filled in later
    chunk_index: int = field(default=0)


def _match_heading(line: str) -> int | None:
    stripped = line.strip()
    if not stripped:
        return None
    for level, pattern in _HEADING_PATTERNS:
        if pattern.match(stripped):
            return level
    return None


def chunk_document(doc: ExtractedDocument) -> list[RawChunk]:
    lines_with_pages: list[tuple[str, int]] = []
    for page in doc.pages:
        for line in page.text.splitlines():
            lines_with_pages.append((line, page.page_number))

    sections = _split_into_sections(lines_with_pages)
    if not sections:
        return _fallback_chunk(doc)
    return _assign_parents(sections)


def _split_into_sections(lines_with_pages: list[tuple[str, int]]) -> list[RawChunk]:
    sections: list[RawChunk] = []
    current_heading: str | None = None
    current_level = 0
    current_page: int | None = None
    buffer: list[str] = []

    def flush():
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                RawChunk(text=text, section_heading=current_heading, page_number=current_page, level=current_level)
            )

    for line, page_number in lines_with_pages:
        level = _match_heading(line)
        if level is not None:
            flush()
            buffer = []
            current_heading = line.strip()
            current_level = level
            current_page = page_number
        else:
            if current_page is None:
                current_page = page_number
            buffer.append(line)
    flush()
    return sections


def _fallback_chunk(doc: ExtractedDocument) -> list[RawChunk]:
    """No recognizable legal structure: group paragraphs up to a target size."""
    chunks: list[RawChunk] = []
    for page in doc.pages:
        paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]
        buf: list[str] = []
        buf_len = 0
        for para in paragraphs:
            if buf_len + len(para) > _FALLBACK_CHUNK_CHARS and buf:
                chunks.append(RawChunk(text="\n\n".join(buf), section_heading=None, page_number=page.page_number, level=0))
                buf, buf_len = [], 0
            buf.append(para)
            buf_len += len(para)
        if buf:
            chunks.append(RawChunk(text="\n\n".join(buf), section_heading=None, page_number=page.page_number, level=0))
    return chunks


def _assign_parents(sections: list[RawChunk]) -> list[RawChunk]:
    """Walk the flat section list and wire up parent_index using a stack keyed
    by heading level, so a level-2 sub-clause points back at its enclosing
    level-1 section, which points back at its level-0 article."""
    stack: list[tuple[int, int]] = []  # (level, index)
    for i, section in enumerate(sections):
        while stack and stack[-1][0] >= section.level:
            stack.pop()
        section.parent_index = stack[-1][1] if stack else None
        section.chunk_index = i
        stack.append((section.level, i))
    return sections
