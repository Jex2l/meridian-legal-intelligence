import os

import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from app.api.main import app
from app.core.db import init_db

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
def client():
    with TestClient(app) as c:
        yield c


def _signup(client, workspace_name, email, name="Test User"):
    resp = client.post(
        "/auth/signup", json={"workspace_name": workspace_name, "email": email, "name": name}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_signup_then_login(client):
    auth = _signup(client, "Firm A", "alice@firma.test")
    assert auth["email"] == "alice@firma.test"

    resp = client.post("/auth/login", json={"email": "alice@firma.test"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == auth["user_id"]


def test_login_unknown_email_is_404(client):
    resp = client.post("/auth/login", json={"email": "nobody@nowhere.test"})
    assert resp.status_code == 404


def test_missing_auth_header_is_401(client):
    resp = client.get("/documents")
    assert resp.status_code == 401


def test_upload_and_list_scoped_to_workspace(client, sample_docx):
    auth_a = _signup(client, "Firm A", "a@firma.test")
    auth_b = _signup(client, "Firm B", "b@firmb.test")
    headers_a = {"Authorization": f"Bearer {auth_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {auth_b['access_token']}"}

    with open(sample_docx, "rb") as f:
        resp = client.post(
            "/documents/upload", headers=headers_a, files={"file": ("contract.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    assert resp.status_code == 200, resp.text
    doc = resp.json()
    assert doc["status"] == "ready"

    resp_a = client.get("/documents", headers=headers_a)
    assert any(d["id"] == doc["id"] for d in resp_a.json())

    resp_b = client.get("/documents", headers=headers_b)
    assert not any(d["id"] == doc["id"] for d in resp_b.json())

    detail_b = client.get(f"/documents/{doc['id']}", headers=headers_b)
    assert detail_b.status_code == 404

    detail_a = client.get(f"/documents/{doc['id']}", headers=headers_a)
    assert detail_a.status_code == 200
    assert len(detail_a.json()["chunks"]) > 0


def test_ask_low_confidence_returns_fallback_without_llm(client, sample_docx):
    auth = _signup(client, "Firm C", "c@firmc.test")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    with open(sample_docx, "rb") as f:
        client.post("/documents/upload", headers=headers, files={"file": ("contract.docx", f)})

    resp = client.post("/ask", headers=headers, json={"question": "What is the capital of France?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["low_confidence"] is True
    assert body["citations"] == []


def test_ask_relevant_question_with_no_provider_returns_503(client, sample_docx, monkeypatch):
    """Forces the "no LLM provider available" path regardless of whether
    this machine happens to have ANTHROPIC_API_KEY set or Ollama running,
    so the test is deterministic in any environment."""
    import app.generation.answer as answer_module

    def _no_provider():
        raise RuntimeError("No LLM provider available (test)")

    monkeypatch.setattr(answer_module, "get_default_provider", _no_provider)

    auth = _signup(client, "Firm D", "d@firmd.test")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    with open(sample_docx, "rb") as f:
        client.post("/documents/upload", headers=headers, files={"file": ("contract.docx", f)})

    resp = client.post("/ask", headers=headers, json={"question": "What does the indemnification clause say?"})
    assert resp.status_code == 503


def _use_fake_provider(monkeypatch, response_text: str) -> None:
    """Swap in a deterministic FakeProvider for /ask so these tests don't
    depend on whether this machine has a real LLM (Anthropic key or Ollama)
    available -- they're testing workspace scoping, not generation quality."""
    import app.generation.answer as answer_module
    from app.generation.provider import FakeProvider

    monkeypatch.setattr(answer_module, "get_default_provider", lambda: FakeProvider(response_text))


def test_spoofed_workspace_id_in_request_body_is_ignored(client, sample_docx, monkeypatch):
    """AskRequest/DraftRequest have no workspace_id field, so even if a
    client stuffs one into the JSON body, FastAPI/Pydantic silently drops
    unknown fields -- the server always resolves workspace_id from the
    verified token, never the request. This test proves the field has zero
    effect, rather than just trusting that it does."""
    _use_fake_provider(monkeypatch, "The Seller must indemnify the Buyer for losses arising from a breach [1].")

    auth_a = _signup(client, "Firm E", "e@firme.test")
    auth_f = _signup(client, "Firm F", "f@firmf.test")
    headers_a = {"Authorization": f"Bearer {auth_a['access_token']}"}
    with open(sample_docx, "rb") as f:
        client.post("/documents/upload", headers=headers_a, files={"file": ("contract.docx", f)})

    # Ask as Firm F (no documents of its own), spoofing Firm A's workspace_id
    # in the body. If the field were honored, this would behave as Firm A's
    # question (relevant -> a real answer); it must instead behave as Firm
    # F's question (nothing relevant -> low_confidence fallback).
    headers_f = {"Authorization": f"Bearer {auth_f['access_token']}"}
    resp = client.post(
        "/ask",
        headers=headers_f,
        json={"question": "What does the indemnification clause say?", "workspace_id": auth_a["workspace_id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["low_confidence"] is True


def test_cross_workspace_question_never_sees_other_workspaces_document(client, sample_docx, monkeypatch):
    _use_fake_provider(monkeypatch, "The Seller must indemnify the Buyer for losses arising from a breach [1].")

    auth_a = _signup(client, "Firm G", "g@firmg.test")
    auth_h = _signup(client, "Firm H", "h@firmh.test")
    headers_a = {"Authorization": f"Bearer {auth_a['access_token']}"}
    headers_h = {"Authorization": f"Bearer {auth_h['access_token']}"}

    with open(sample_docx, "rb") as f:
        client.post("/documents/upload", headers=headers_a, files={"file": ("contract.docx", f)})

    # Firm H has no documents at all; the same question that gets a real,
    # cited answer for Firm A must fall back to low-confidence for Firm H,
    # proving Firm A's chunks never entered Firm H's retrieval candidate set.
    resp_a = client.post("/ask", headers=headers_a, json={"question": "What does the indemnification clause say?"})
    resp_h = client.post("/ask", headers=headers_h, json={"question": "What does the indemnification clause say?"})

    assert resp_a.status_code == 200
    assert resp_a.json()["low_confidence"] is False
    assert len(resp_a.json()["citations"]) > 0
    assert resp_h.status_code == 200
    assert resp_h.json()["low_confidence"] is True


def test_ask_with_blank_question_is_rejected(client):
    auth = _signup(client, "Firm I", "i@firmi.test")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    resp = client.post("/ask", headers=headers, json={"question": "   "})
    assert resp.status_code == 422


def test_upload_rejects_oversized_file(client, monkeypatch):
    import app.api.routers.documents as documents_module

    monkeypatch.setattr(documents_module, "MAX_UPLOAD_BYTES", 10)  # 10 bytes, trivially exceeded
    auth = _signup(client, "Firm J", "j@firmj.test")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    resp = client.post(
        "/documents/upload", headers=headers,
        files={"file": ("big.docx", b"x" * 1000, "application/octet-stream")},
    )
    assert resp.status_code == 413
