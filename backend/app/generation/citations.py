"""Validate that every citation marker the LLM emitted resolves to a real
retrieved chunk. This is the check that keeps the "never invent a citation"
rule from being just a prompt instruction -- answers with an out-of-range
citation are flagged rather than trusted.
"""

import re
from dataclasses import dataclass

from app.retrieval.search import RetrievedChunk

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


@dataclass
class Citation:
    marker: str  # e.g. "[1]"
    index: int  # 1-based, as it appeared in the text
    chunk: RetrievedChunk


@dataclass
class ValidationResult:
    citations: list[Citation]
    invalid_indices: list[int]  # cited but out of range of the retrieved set

    @property
    def is_fully_grounded(self) -> bool:
        return len(self.invalid_indices) == 0


def extract_and_validate_citations(answer_text: str, chunks: list[RetrievedChunk]) -> ValidationResult:
    found_indices = {int(m.group(1)) for m in _CITATION_PATTERN.finditer(answer_text)}

    citations: list[Citation] = []
    invalid: list[int] = []
    for idx in sorted(found_indices):
        if 1 <= idx <= len(chunks):
            citations.append(Citation(marker=f"[{idx}]", index=idx, chunk=chunks[idx - 1]))
        else:
            invalid.append(idx)
    return ValidationResult(citations=citations, invalid_indices=invalid)
