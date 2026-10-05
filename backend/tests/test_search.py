import os

import pytest
import sqlalchemy

from app.core.db import init_db
from app.ingestion.pipeline import ingest_file
from app.models.models import SourceType, User, Workspace
from app.retrieval.search import SearchFilters, hybrid_search

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
def two_workspaces_with_docs(db_session, sample_docx, sample_pdf):
    ws_a = Workspace(name="Firm A - Indemnity Research")
    ws_b = Workspace(name="Firm B - Unrelated")
    db_session.add_all([ws_a, ws_b])
    db_session.flush()
    user_a = User(workspace_id=ws_a.id, email="a@a.com", name="A")
    user_b = User(workspace_id=ws_b.id, email="b@b.com", name="B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # sample_docx contains an "Indemnification" section -- put it only in workspace A.
    ingest_file(
        db_session, src_path=sample_docx, filename="indemnity.docx",
        workspace_id=ws_a.id, owner_user_id=user_a.id, embed=True,
    )
    # sample_pdf has unrelated content -- put it only in workspace B.
    ingest_file(
        db_session, src_path=sample_pdf, filename="memo.pdf",
        workspace_id=ws_b.id, owner_user_id=user_b.id, embed=True,
    )
    return ws_a, ws_b


def test_hybrid_search_finds_relevant_chunk(db_session, two_workspaces_with_docs):
    ws_a, _ws_b = two_workspaces_with_docs
    results = hybrid_search(db_session, "indemnification losses breach", ws_a.id, k=3, use_reranker=False)
    assert len(results) > 0
    assert any("indemnif" in r.text.lower() for r in results)


def test_hybrid_search_never_returns_other_workspace_chunks(db_session, two_workspaces_with_docs):
    ws_a, ws_b = two_workspaces_with_docs
    results_a = hybrid_search(db_session, "indemnification losses breach", ws_a.id, k=10, use_reranker=False)
    results_b = hybrid_search(db_session, "indemnification losses breach", ws_b.id, k=10, use_reranker=False)

    # Chunks with workspace_id=None belong to the public corpus and are
    # legitimately visible from any workspace; a chunk belonging to the
    # OTHER private workspace must never appear.
    assert all(r.workspace_id in (ws_a.id, None) for r in results_a)
    assert all(r.workspace_id in (ws_b.id, None) for r in results_b)
    # The indemnity chunk belongs only to workspace A, so B must never see it.
    assert not any("indemnif" in r.text.lower() for r in results_b)


def test_reranker_reorders_candidates(db_session, two_workspaces_with_docs):
    ws_a, _ws_b = two_workspaces_with_docs
    results = hybrid_search(db_session, "indemnification losses breach", ws_a.id, k=3, use_reranker=True)
    assert all(r.rerank_score is not None for r in results)


def test_use_reranker_none_defers_to_settings(monkeypatch, db_session, two_workspaces_with_docs):
    """use_reranker=None (the default for answer_question()/draft()'s
    callers) must defer to settings.enable_reranker, and when that's
    False, the cross-encoder must never be invoked -- this is what lets
    production run without sentence-transformers/torch installed at all
    (see requirements-render.txt)."""
    import app.retrieval.search as search_module

    ws_a, _ws_b = two_workspaces_with_docs

    def exploding_rerank(*args, **kwargs):
        raise AssertionError("cross-encoder must not be called when enable_reranker is False")

    monkeypatch.setattr(search_module.settings, "enable_reranker", False)
    monkeypatch.setattr(search_module, "cross_encoder_rerank", exploding_rerank)

    results = hybrid_search(db_session, "indemnification losses breach", ws_a.id, k=3)
    assert len(results) > 0
    assert all(r.rerank_score is None for r in results)


def test_jurisdiction_filter_applied_in_query(db_session, two_workspaces_with_docs):
    ws_a, _ws_b = two_workspaces_with_docs
    results = hybrid_search(
        db_session, "indemnification", ws_a.id, k=5, use_reranker=False,
        filters=SearchFilters(jurisdiction="Delaware"),
    )
    # No document was tagged with this jurisdiction, so the filter (applied
    # inside the SQL WHERE clause) must exclude everything.
    assert results == []
