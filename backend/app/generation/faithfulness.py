"""Claim-span faithfulness check: does the text around each citation in a
generated answer actually say something its cited passage supports?

Citation validation (citations.py) only checks that a cited index resolves
to a real retrieved chunk -- it says nothing about whether the cited
passage actually supports the specific claim attached to it. This module
closes that gap using the cross-encoder reranker as a cheap entailment
proxy (reusing the exact model/scoring already used for retrieval
reranking and the retrieval confidence gate, so no extra model is
needed).

The unit of analysis is a "claim span": a citation-bearing sentence plus
any immediately following sentences that carry no citation marker of
their own, up to the next citation-bearing sentence or the end of the
text. Two earlier, simpler designs were tried and found wrong via live
testing:
  - Sentence-level: a model commonly writes a short lead sentence with the
    citation ("Yes, there is a cap on liability [1].") followed by an
    uncited explanatory sentence with the actual supporting detail. Scored
    alone, the bare lead sentence didn't resemble the passage even though
    the full claim was correct -- a false rejection.
  - Paragraph-level: fixed the above, but then scoring an entire paragraph
    against EACH of several distinct citations it contains dilutes every
    claim with the others' unrelated text, including the ones that were
    genuinely correct -- see tests/test_faithfulness.py for both cases.
Claim spans keep a citation and its own trailing explanation together
without merging in a different citation's claim.

Used both live (answer.py/draft.py gate a response on this) and by the
eval harness (app/eval/metrics.py imports from here, not the other way
around -- eval is the outer testing layer and should depend on
generation, not vice versa).
"""

import re

from app.generation.citations import extract_and_validate_citations
from app.retrieval.reranker import rerank as cross_encoder_score
from app.retrieval.search import RetrievedChunk

# Cross-encoder (ms-marco-MiniLM-L-6-v2) outputs raw logits, not probabilities.
# A positive score says a claim span reads as entailed by/relevant to the
# passage it cites -- the same reasoning used for the retrieval confidence
# gate (see app/generation/confidence.py).
FAITHFULNESS_THRESHOLD = 0.0

# An answer is rejected only if a MAJORITY of its claim spans fail the
# check, not on a single failure -- a 100%-required gate would reject too
# many good answers on reranker noise alone. A majority-fail gate still
# catches answers that are substantially unsupported.
FAITHFULNESS_MIN_RATIO = 0.5

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_HAS_CITATION = re.compile(r"\[\d+\]")
_CITATION_ONLY = re.compile(r"^[\[\]\d\s.,;:]*$")  # e.g. "[1]" or "[1][2]." with nothing else


def _is_citation_only(sentence: str) -> bool:
    """True for a 'sentence' that's just citation markers and stray
    punctuation, with no real content of its own -- produced when a model
    writes 'claim. [1]' (period BEFORE the bracket) instead of 'claim [1].'
    (bracket before the period): naive sentence-splitting on '.' then
    orphans '[1]' into its own fragment. Scored alone, a bare bracket has
    no semantic content and trivially fails the faithfulness check
    regardless of how well-supported the actual claim is -- a false
    rejection, found via live testing, not a real lack of support."""
    return bool(_CITATION_ONLY.match(sentence.strip()))


def _claim_spans(answer_text: str) -> list[str]:
    """Groups sentences into spans in two passes.

    Pass 1 repairs a splitting artifact: "claim. [1]" (period BEFORE the
    bracket) splits into "claim." (no citation) and "[1]" (no content) --
    the content sentence would otherwise be dropped as "uncited" before
    the citation fragment is even reached, and the bare bracket would
    start its own content-free span. Found via live testing. A
    citation-only fragment is re-glued onto whatever sentence immediately
    preceded it, regardless of whether that sentence had a citation of its
    own, undoing the bad split.

    Pass 2 groups the repaired sentences into spans: a citation-bearing
    sentence absorbs any immediately following sentences that carry no
    citation marker of their own (the normal "claim [1]. Explanation."
    pattern). Leading uncited sentences (before the first citation) are
    dropped -- there's nothing to check them against.
    """
    raw_sentences = _SENTENCE_SPLIT.split(answer_text.strip())

    merged: list[str] = []
    for sentence in raw_sentences:
        if _is_citation_only(sentence) and merged:
            merged[-1] = merged[-1] + " " + sentence
        else:
            merged.append(sentence)

    spans: list[str] = []
    for sentence in merged:
        if _HAS_CITATION.search(sentence):
            spans.append(sentence)
        elif spans:
            spans[-1] = spans[-1] + " " + sentence
    return spans


def faithfulness_score(answer_text: str, retrieved: list[RetrievedChunk]) -> tuple[int, int]:
    """Returns (faithful_count, total_count) over (claim span, citation)
    pairs. Each distinct citation index within a span is scored by
    checking the span's full text (its lead sentence plus any trailing
    unmarked explanation) against that citation's passage."""
    total = 0
    faithful = 0
    for span in _claim_spans(answer_text):
        validation = extract_and_validate_citations(span, retrieved)
        seen_indices: set[int] = set()
        for citation in validation.citations:
            if citation.index in seen_indices:
                continue
            seen_indices.add(citation.index)
            total += 1
            score = cross_encoder_score(span, [citation.chunk.text])[0]
            if score > FAITHFULNESS_THRESHOLD:
                faithful += 1
    return faithful, total


def is_answer_faithful(answer_text: str, retrieved: list[RetrievedChunk], min_ratio: float = FAITHFULNESS_MIN_RATIO) -> bool:
    """Live gate: True unless a majority of claim spans fail the
    faithfulness check. An answer with no citations at all (e.g. the
    no-support fallback) is trivially faithful -- that case is handled
    separately by the citation-requirement gate."""
    faithful, total = faithfulness_score(answer_text, retrieved)
    if total == 0:
        return True
    return (faithful / total) >= min_ratio
