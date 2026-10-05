from app.retrieval.search import RetrievedChunk

# Cross-encoder (ms-marco-MiniLM-L-6-v2) outputs raw logits, not probabilities.
#
# These thresholds were originally picked from a single hand example each
# (0.0 for Ask, -8.0 for Draft) and turned out to be miscalibrated: real
# user testing found a genuinely correct match ("Is there a cap on
# liability?" -> the Limitation of Liability clause) scoring -5.03, well
# below the old 0.0 cutoff, causing a true positive to be wrongly rejected
# as low-confidence.
#
# Recalibrated against real score data gathered across the 36-item eval set
# plus targeted single-document-workspace probes (see README, "Phase 9"):
#   - Natural-language questions: true positives ranged from -5.03 up to
#     +10.65; true negatives (genuinely unrelated questions) clustered
#     tightly around -11. -8.0 sits in the gap with margin on both sides.
#   - Imperative drafting instructions ("rewrite the X clause to Y") score
#     markedly lower even for true positives (observed as low as -9.80),
#     and -- importantly -- their score distribution OVERLAPS with
#     irrelevant imperative queries (an unrelated "add a clause about
#     alien spacecraft liability" scored -7.23, higher than a genuine
#     match). No clean separating threshold exists for imperative queries
#     with this reranker; -10.5 is a best-effort floor that mainly catches
#     "nothing at all relevant was retrieved" rather than reliably
#     distinguishing relevant from irrelevant drafting requests. The real
#     safety net for drafting is the system prompt's explicit instruction
#     to say so when passages don't support a draft, plus citation
#     validation rejecting any fabricated citation.
DEFAULT_CONFIDENCE_THRESHOLD = -8.0
DRAFTING_CONFIDENCE_THRESHOLD = -10.5


def is_low_confidence(chunks: list[RetrievedChunk], threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> bool:
    if not chunks:
        return True
    top = chunks[0]
    if top.rerank_score is not None:
        return top.rerank_score < threshold
    return top.fused_score <= 0.0
