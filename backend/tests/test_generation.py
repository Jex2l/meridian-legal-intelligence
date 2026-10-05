import os

import pytest
import sqlalchemy

from app.core.db import init_db
from app.generation.answer import answer_question
from app.generation.citations import extract_and_validate_citations
from app.generation.draft import draft
from app.generation.prompts import NO_SUPPORT_MESSAGE
from app.generation.provider import FakeProvider
from app.ingestion.pipeline import ingest_file
from app.models.models import User, Workspace

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


@pytest.fixture
def db_session():
    from app.core.db import SessionLocal

    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def workspace_with_indemnity_doc(db_session, sample_docx):
    ws = Workspace(name="Firm")
    db_session.add(ws)
    db_session.flush()
    user = User(workspace_id=ws.id, email="t@t.com", name="T")
    db_session.add(user)
    db_session.commit()
    ingest_file(
        db_session, src_path=sample_docx, filename="indemnity.docx",
        workspace_id=ws.id, owner_user_id=user.id, embed=True,
    )
    return ws


def test_answer_with_valid_citation_is_accepted(db_session, workspace_with_indemnity_doc):
    ws = workspace_with_indemnity_doc
    provider = FakeProvider("The seller must indemnify the buyer for breach-related losses [1].")
    result = answer_question(db_session, "What does the indemnification clause say?", ws.id, provider=provider)

    assert not result.low_confidence
    assert not result.ungrounded_response_rejected
    assert "[1]" in result.answer_text
    assert result.validation.is_fully_grounded


def test_answer_with_invented_citation_is_rejected(db_session, workspace_with_indemnity_doc):
    ws = workspace_with_indemnity_doc
    # [99] cannot exist -- at most k=5 passages are ever retrieved.
    provider = FakeProvider("This is backed by a passage [99] that was never retrieved.")
    result = answer_question(db_session, "What does the indemnification clause say?", ws.id, provider=provider)

    assert result.ungrounded_response_rejected
    assert result.answer_text == NO_SUPPORT_MESSAGE
    assert 99 in result.validation.invalid_indices


def test_low_confidence_skips_llm_call_entirely(db_session, workspace_with_indemnity_doc):
    ws = workspace_with_indemnity_doc

    class ExplodingProvider:
        def generate(self, *a, **kw):
            raise AssertionError("LLM should never be called when retrieval confidence is low")

    result = answer_question(
        db_session,
        "What is the capital of France?",  # unrelated to the ingested document
        ws.id,
        provider=ExplodingProvider(),
    )
    assert result.low_confidence
    assert result.answer_text == NO_SUPPORT_MESSAGE


def test_draft_mode_produces_cited_draft(db_session, workspace_with_indemnity_doc):
    ws = workspace_with_indemnity_doc
    provider = FakeProvider(
        "Draft: Each party shall indemnify the other only for losses from its own gross negligence [1].\n\n"
        "Reasoning: This mirrors the existing clause [1]."
    )
    result = draft(db_session, "Rewrite the indemnification clause", ws.id, provider=provider)
    assert not result.low_confidence
    assert "Reasoning" in result.draft_text
    assert result.validation.is_fully_grounded


def test_citation_extraction_deduplicates_and_sorts():
    from app.retrieval.search import RetrievedChunk
    import uuid as _uuid

    chunks = [
        RetrievedChunk(
            chunk_id=_uuid.uuid4(), document_id=_uuid.uuid4(), workspace_id=None,
            text="a", section_heading=None, page_number=1, document_filename="f",
        )
    ]
    result = extract_and_validate_citations("See [1] and again [1].", chunks)
    assert len(result.citations) == 1
    assert result.citations[0].index == 1
