"""Drafting mode: same retrieve -> generate -> validate pipeline as Q&A, but
with a drafting-specific prompt that asks for a draft plus a cited
reasoning section instead of a direct answer.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.generation.citations import ValidationResult, extract_and_validate_citations
from app.generation.confidence import DRAFTING_CONFIDENCE_THRESHOLD, is_low_confidence
from app.generation.prompts import DRAFTING_SYSTEM_PROMPT, NO_SUPPORT_MESSAGE, build_drafting_prompt
from app.generation.provider import LLMProvider, get_default_provider
from app.retrieval.search import RetrievedChunk, SearchFilters, hybrid_search


@dataclass
class DraftResult:
    task: str
    draft_text: str
    retrieved_chunks: list[RetrievedChunk]
    validation: ValidationResult | None
    low_confidence: bool
    ungrounded_response_rejected: bool = False


def draft(
    session: Session,
    task: str,
    workspace_id: uuid.UUID,
    provider: LLMProvider | None = None,
    k: int = 6,
    filters: SearchFilters | None = None,
    confidence_threshold: float = DRAFTING_CONFIDENCE_THRESHOLD,
) -> DraftResult:
    retrieved = hybrid_search(session, task, workspace_id, k=k, filters=filters)

    if is_low_confidence(retrieved, confidence_threshold):
        return DraftResult(
            task=task,
            draft_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=None,
            low_confidence=True,
        )

    provider = provider or get_default_provider()
    user_prompt = build_drafting_prompt(task, retrieved)
    raw_draft = provider.generate(DRAFTING_SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    validation = extract_and_validate_citations(raw_draft, retrieved)
    if not validation.is_fully_grounded:
        return DraftResult(
            task=task,
            draft_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=validation,
            low_confidence=False,
            ungrounded_response_rejected=True,
        )

    return DraftResult(
        task=task,
        draft_text=raw_draft,
        retrieved_chunks=retrieved,
        validation=validation,
        low_confidence=False,
    )
