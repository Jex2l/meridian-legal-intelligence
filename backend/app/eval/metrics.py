"""Eval metrics: retrieval recall@k/precision@k, citation accuracy, and a
faithfulness check. Faithfulness and citation accuracy need an actual LLM
answer to evaluate, so they're skipped when no provider is configured;
retrieval metrics never need the LLM and always run.
"""

from dataclasses import dataclass

from app.eval.fixtures import GoldItem
from app.generation.citations import extract_and_validate_citations
from app.generation.faithfulness import faithfulness_score  # noqa: F401  (re-exported for callers of this module)
from app.retrieval.search import RetrievedChunk


def _is_gold_chunk(chunk: RetrievedChunk, gold: GoldItem) -> bool:
    return chunk.document_filename == gold.gold_filename and gold.gold_text_substring in chunk.text


@dataclass
class RetrievalEvalRow:
    gold_id: str
    found_at_rank: int | None  # 1-based rank of the gold chunk, None if not found in top-k


def retrieval_recall_at_k(rows: list[RetrievalEvalRow]) -> float:
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.found_at_rank is not None) / len(rows)


def retrieval_precision_at_k(rows: list[RetrievalEvalRow], k: int) -> float:
    """Mean, over items, of (1 if the single known-relevant chunk was
    retrieved else 0) / k -- the standard precision@k for a one-relevant-
    document eval set."""
    if not rows:
        return 0.0
    return sum((1.0 / k) if r.found_at_rank is not None else 0.0 for r in rows) / len(rows)


def mean_reciprocal_rank(rows: list[RetrievalEvalRow]) -> float:
    if not rows:
        return 0.0
    return sum((1.0 / r.found_at_rank) if r.found_at_rank is not None else 0.0 for r in rows) / len(rows)


def citation_points_to_gold(answer_text: str, retrieved: list[RetrievedChunk], gold: GoldItem) -> bool:
    """True if at least one citation in the answer resolves to the gold chunk."""
    validation = extract_and_validate_citations(answer_text, retrieved)
    return any(_is_gold_chunk(c.chunk, gold) for c in validation.citations)
