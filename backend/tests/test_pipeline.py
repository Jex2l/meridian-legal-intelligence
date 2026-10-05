import os

import pytest
import sqlalchemy
from sqlalchemy import text as sql_text

from app.core.db import Base, engine, init_db
from app.ingestion.pipeline import IngestionError, ingest_file
from app.models.models import Document, SourceType, User, Workspace

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
def workspace_and_user(db_session):
    ws = Workspace(name="Test Firm")
    db_session.add(ws)
    db_session.flush()
    user = User(workspace_id=ws.id, email="t@test.com", name="Tess Ter")
    db_session.add(user)
    db_session.commit()
    return ws, user


def test_ingest_upload_requires_workspace_and_user(db_session, sample_docx):
    with pytest.raises(IngestionError):
        ingest_file(
            db_session,
            src_path=sample_docx,
            filename="sample.docx",
            workspace_id=None,
            owner_user_id=None,
        )


def test_ingest_docx_creates_document_and_chunks(db_session, workspace_and_user, sample_docx):
    ws, user = workspace_and_user
    document = ingest_file(
        db_session,
        src_path=sample_docx,
        filename="sample.docx",
        workspace_id=ws.id,
        owner_user_id=user.id,
    )
    assert document.status == "ready"
    assert len(document.chunks) >= 3
    assert all(c.workspace_id == ws.id for c in document.chunks)


def test_ingest_public_corpus_has_no_workspace(db_session, sample_pdf):
    document = ingest_file(
        db_session,
        src_path=sample_pdf,
        filename="case.pdf",
        workspace_id=None,
        owner_user_id=None,
        source_type=SourceType.PUBLIC_CORPUS,
    )
    assert document.workspace_id is None
    assert all(c.workspace_id is None for c in document.chunks)


def test_two_workspaces_documents_are_distinct(db_session, sample_docx, sample_pdf):
    ws_a = Workspace(name="Firm A")
    ws_b = Workspace(name="Firm B")
    db_session.add_all([ws_a, ws_b])
    db_session.flush()
    user_a = User(workspace_id=ws_a.id, email="a@a.com", name="A")
    user_b = User(workspace_id=ws_b.id, email="b@b.com", name="B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    doc_a = ingest_file(
        db_session, src_path=sample_docx, filename="a.docx", workspace_id=ws_a.id, owner_user_id=user_a.id
    )
    doc_b = ingest_file(
        db_session, src_path=sample_pdf, filename="b.pdf", workspace_id=ws_b.id, owner_user_id=user_b.id
    )

    rows = db_session.execute(
        sql_text("SELECT workspace_id FROM chunks WHERE workspace_id = :wid"), {"wid": str(ws_a.id)}
    ).fetchall()
    assert len(rows) == len(doc_a.chunks)
    assert str(ws_b.id) not in [str(r[0]) for r in rows]
