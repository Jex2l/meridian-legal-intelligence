"""Validate that every citation marker the LLM emitted resolves to a real
retrieved chunk. This is the check that keeps the "never invent a citation"
rule from being just a prompt instruction -- answers with an out-of-range
citation are flagged rather than trusted.
"""

import re
from dataclasses import dataclass

from app.retrieval.search import RetrievedChunk

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")

# The LLM is instructed to cite as ASCII "[1]", but was observed live
# (Groq's openai/gpt-oss-120b) occasionally emitting Unicode lookalike
# brackets instead -- e.g. "【1】" (CJK lenticular brackets) or
# fullwidth "［1］". Those don't match _CITATION_PATTERN, so an
# otherwise fully-grounded answer was wrongly rejected as having "no
# citation". Normalizing to ASCII brackets right after generation, before
# any validation, fixes this for citations.py, faithfulness.py, and the
# frontend's own "[\d+]" parser in one place.
_BRACKET_LOOKALIKES = str.maketrans({"【": "[", "】": "]", "［": "[", "］": "]"})


def normalize_citation_brackets(text: str) -> str:
    return text.translate(_BRACKET_LOOKALIKES)


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
