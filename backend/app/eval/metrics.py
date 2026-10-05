"""Eval metrics: retrieval recall@k/precision@k, citation accuracy, and a
faithfulness check. Faithfulness and citation accuracy need an actual LLM
answer to evaluate, so they're skipped when no provider is configured;
retrieval metrics never need the LLM and always run.
"""

from dataclasses import dataclass

from app.eval.fixtures import GoldItem
from app.generation.citations import extract_and_validate_citations
from app.retrieval.reranker import rerank as cross_encoder_score
from app.retrieval.search import RetrievedChunk

# Reuse the cross-encoder as a cheap faithfulness proxy: does this sentence
# read as entailed by this passage? A positive logit says yes, mirroring
# the same reasoning used for the retrieval confidence gate.
FAITHFULNESS_THRESHOLD = 0.0


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


def faithfulness_score(answer_text: str, retrieved: list[RetrievedChunk]) -> tuple[int, int]:
    """Returns (faithful_sentence_count, total_cited_sentence_count).

    Splits the answer into sentences, keeps the ones carrying a citation
    marker, and scores each sentence against its cited passage(s) with the
    cross-encoder. A sentence is "faithful" if its best-matching cited
    passage scores above FAITHFULNESS_THRESHOLD.
    """
    import re

    sentences = re.split(r"(?<=[.!?])\s+", answer_text.strip())
    cited_sentences = [s for s in sentences if re.search(r"\[\d+\]", s)]
    if not cited_sentences:
        return 0, 0

    total = 0
    faithful = 0
    for sentence in cited_sentences:
        validation = extract_and_validate_citations(sentence, retrieved)
        if not validation.citations:
            continue
        total += 1
        passages = [c.chunk.text for c in validation.citations]
        scores = cross_encoder_score(sentence, passages)
        if max(scores) > FAITHFULNESS_THRESHOLD:
            faithful += 1
    return faithful, total
