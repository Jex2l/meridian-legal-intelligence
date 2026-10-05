from app.retrieval.search import RetrievedChunk

# Cross-encoder (ms-marco-MiniLM-L-6-v2) outputs raw logits, not probabilities.
# Empirically, a genuinely relevant passage scores positive and an unrelated
# one scores strongly negative (see README) -- 0.0 is a conservative cutoff
# for natural-language questions.
DEFAULT_CONFIDENCE_THRESHOLD = 0.0

# The reranker is trained on question-style queries. A drafting instruction
# ("rewrite the indemnity clause") is phrased as an imperative, not a
# question, so it scores a genuinely relevant passage markedly lower than an
# equivalent question would -- empirically still well clear of an unrelated
# passage's score (around -11 in this corpus), so a looser threshold here
# still catches "nothing relevant was found" without flagging every draft.
DRAFTING_CONFIDENCE_THRESHOLD = -8.0


def is_low_confidence(chunks: list[RetrievedChunk], threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> bool:
    if not chunks:
        return True
    top = chunks[0]
    if top.rerank_score is not None:
        return top.rerank_score < threshold
    return top.fused_score <= 0.0
