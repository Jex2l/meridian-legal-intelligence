"""Cross-encoder reranking: scores (query, passage) pairs jointly, which is
more accurate than cosine/BM25 similarity alone but too slow to run over an
entire corpus -- so it only runs over the fused candidate shortlist.
"""

from functools import lru_cache


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query: str, passages: list[str]) -> list[float]:
    """Returns a relevance score per passage, same order as input."""
    if not passages:
        return []
    pairs = [(query, p) for p in passages]
    scores = _model().predict(pairs)
    return [float(s) for s in scores]
