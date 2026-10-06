import os
import uuid

import pytest
import sqlalchemy

from app.core.db import init_db
from app.generation import faithfulness as faithfulness_module
from app.generation.faithfulness import faithfulness_score, is_answer_faithful
from app.retrieval.search import RetrievedChunk

pytestmark = pytest.mark.skipif(
    os.environ.get("LEXRAG_SKIP_DB_TESTS") == "1",
    reason="DB not available",
)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db():
    try:
        init_db()
    except sqlalchemy.exc.OperationalError:
        pytest.skip("Postgres is not reachable; start it with `docker compose up -d`")
    yield


def _chunk(text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(), document_id=uuid.uuid4(), workspace_id=None,
        text=text, section_heading="Indemnification", page_number=1, document_filename="f.docx",
    )


def test_faithful_sentence_scores_as_faithful():
    chunks = [_chunk("Each party shall indemnify the other for losses caused by its own gross negligence.")]
    answer = "Each party must indemnify the other for losses from its own gross negligence [1]."
    faithful, total = faithfulness_score(answer, chunks)
    assert total == 1
    assert faithful == 1
    assert is_answer_faithful(answer, chunks) is True


def test_unfaithful_sentence_scores_as_unfaithful():
    chunks = [_chunk("Each party shall indemnify the other for losses caused by its own gross negligence.")]
    answer = "The moon is made of cheese according to this clause [1]."
    faithful, total = faithfulness_score(answer, chunks)
    assert total == 1
    assert faithful == 0
    assert is_answer_faithful(answer, chunks) is False


def test_uncited_text_is_not_scored_at_all():
    chunks = [_chunk("Each party shall indemnify the other for losses caused by its own gross negligence.")]
    answer = "This sentence has no citation marker at all."
    faithful, total = faithfulness_score(answer, chunks)
    assert total == 0
    assert faithful == 0
    # No cited sentences to check -- trivially faithful, handled by the
    # separate "no citations at all" gate instead.
    assert is_answer_faithful(answer, chunks) is True


def test_short_lead_sentence_plus_explanation_in_one_paragraph_is_faithful():
    """Regression test for a real false-rejection found via live testing:
    a short lead sentence carries the citation marker, and the actual
    supporting detail is in the very next sentence of the SAME paragraph,
    with no marker of its own. Scoring sentence-by-sentence previously
    rejected this because the bare lead sentence alone didn't resemble the
    passage; paragraph-level grouping must accept it."""
    chunks = [_chunk("Neither party's aggregate liability under this Agreement shall exceed the total fees paid.")]
    answer = (
        "Yes, there is a cap on liability [1]. According to the agreement, neither party's "
        "aggregate liability under this Agreement shall exceed the total fees paid."
    )
    assert is_answer_faithful(answer, chunks) is True


def test_citation_marker_after_period_is_not_orphaned():
    """Regression test for a real false-rejection found via live testing:
    a model wrote "...conflict of laws principles. [1]" -- period BEFORE
    the bracket, not after. Naive sentence-splitting on '.' then produces
    two fragments: the full claim with NO citation (dropped as "leading
    uncited"), and a bare "[1]" with NO content (scores as unfaithful on
    its own, since a lone bracket has no semantic content). The fix must
    re-glue the bracket onto the sentence that precedes it."""
    chunks = [_chunk(
        "This Agreement shall be governed by and construed in accordance with the laws of the "
        "State of New York, without regard to its conflict of laws principles."
    )]
    answer = (
        "This Agreement shall be governed by and construed in accordance with the laws of the "
        "State of New York, without regard to its conflict of laws principles. [1]"
    )
    faithful, total = faithfulness_score(answer, chunks)
    assert total == 1
    assert faithful == 1
    assert is_answer_faithful(answer, chunks) is True


def test_majority_rule_across_distinct_citations_in_one_paragraph():
    liability_chunk = _chunk("Neither party's aggregate liability under this Agreement shall exceed the total fees paid.")
    termination_chunk = _chunk("This Agreement shall remain in effect for one year and may be terminated upon notice.")
    scope_chunk = _chunk("Consultant shall provide advisory services related to corporate restructuring.")
    chunks = [liability_chunk, termination_chunk, scope_chunk]

    # One real, on-topic claim ([1], with its own brief elaboration -- a
    # bare one-line claim is a known weak spot for the cross-encoder
    # regardless of correctness, see the short-lead-sentence test above)
    # plus two short nonsense claims misattributed to unrelated real
    # chunks ([2], [3]). Each citation gets its own span, so the elaborated
    # correct claim isn't dragged down by the nonsense ones next to it.
    answer = (
        "There is a cap on liability, limited to total fees paid under the agreement [1]. "
        "The agreement also establishes a colony on Mars [2]. "
        "This clause grants unlimited free coffee to all employees [3]."
    )
    faithful, total = faithfulness_score(answer, chunks)
    assert total == 3
    assert faithful == 1
    assert is_answer_faithful(answer, chunks) is False


def test_is_answer_faithful_skips_cross_encoder_when_reranker_disabled(monkeypatch):
    """Regression test for a real production bug: ENABLE_RERANKER=false
    (set to keep retrieval within a RAM-constrained host's budget) must
    disable EVERY caller of the cross-encoder model, not just retrieval
    reranking. Found live: is_answer_faithful() still tried to import
    sentence_transformers (not installed in that configuration) and
    crashed every /ask request with ModuleNotFoundError -> 500."""
    chunks = [_chunk("Each party shall indemnify the other for losses caused by its own gross negligence.")]
    answer = "The moon is made of cheese according to this clause [1]."  # would normally score unfaithful

    def exploding_rerank(*args, **kwargs):
        raise AssertionError("cross-encoder must not be invoked when enable_reranker is False")

    monkeypatch.setattr(faithfulness_module.settings, "enable_reranker", False)
    monkeypatch.setattr(faithfulness_module, "cross_encoder_score", exploding_rerank)

    # Must return True (trivially faithful, same as "no cited sentences")
    # instead of raising or actually scoring the claim.
    assert is_answer_faithful(answer, chunks) is True
