"""Grounded answer generation: retrieve -> prompt -> generate -> validate
citations against the retrieved set -> low-confidence fallback.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.generation.citations import ValidationResult, extract_and_validate_citations
from app.generation.confidence import DEFAULT_CONFIDENCE_THRESHOLD, is_low_confidence
from app.generation.faithfulness import is_answer_faithful
from app.generation.prompts import NO_SUPPORT_MESSAGE, SYSTEM_PROMPT, build_user_prompt
from app.generation.provider import LLMProvider, get_default_provider
from app.retrieval.search import RetrievedChunk, SearchFilters, hybrid_search


@dataclass
class AnswerResult:
    question: str
    answer_text: str
    retrieved_chunks: list[RetrievedChunk]
    validation: ValidationResult | None
    low_confidence: bool
    ungrounded_response_rejected: bool = False
    rejection_reason: str | None = None  # "invalid_citation" | "no_citation" | "unfaithful", when rejected


def answer_question(
    session: Session,
    question: str,
    workspace_id: uuid.UUID,
    provider: LLMProvider | None = None,
    k: int = 5,
    filters: SearchFilters | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> AnswerResult:
    retrieved = hybrid_search(session, question, workspace_id, k=k, filters=filters)

    if is_low_confidence(retrieved, confidence_threshold):
        return AnswerResult(
            question=question,
            answer_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=None,
            low_confidence=True,
        )

    provider = provider or get_default_provider()
    user_prompt = build_user_prompt(question, retrieved)
    raw_answer = provider.generate(SYSTEM_PROMPT, user_prompt)

    validation = extract_and_validate_citations(raw_answer, retrieved)

    if not validation.is_fully_grounded:
        # The model cited a passage number outside the retrieved set -- per
        # "never invent a citation", we don't trust this answer at all.
        return AnswerResult(
            question=question,
            answer_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=validation,
            low_confidence=False,
            ungrounded_response_rejected=True,
            rejection_reason="invalid_citation",
        )

    is_no_support = raw_answer.strip() == NO_SUPPORT_MESSAGE
    if not is_no_support and not validation.citations:
        # The model made claims with zero citation markers at all -- the
        # prompt requires one per claim, so an answer with none is treated
        # as uncited, not as "no invalid citations found."
        return AnswerResult(
            question=question,
            answer_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=validation,
            low_confidence=False,
            ungrounded_response_rejected=True,
            rejection_reason="no_citation",
        )

    if not is_no_support and not is_answer_faithful(raw_answer, retrieved):
        # A majority of cited sentences don't actually read as supported by
        # their own cited passage (per the cross-encoder faithfulness
        # check) -- the citation exists, but the claim attached to it
        # likely doesn't match what the passage says.
        return AnswerResult(
            question=question,
            answer_text=NO_SUPPORT_MESSAGE,
            retrieved_chunks=retrieved,
            validation=validation,
            low_confidence=False,
            ungrounded_response_rejected=True,
            rejection_reason="unfaithful",
        )

    return AnswerResult(
        question=question,
        answer_text=raw_answer,
        retrieved_chunks=retrieved,
        validation=validation,
        low_confidence=False,
    )
