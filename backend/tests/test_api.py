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


def test_ask_relevant_question_without_api_key_returns_503(client, sample_docx):
    auth = _signup(client, "Firm D", "d@firmd.test")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    with open(sample_docx, "rb") as f:
        client.post("/documents/upload", headers=headers, files={"file": ("contract.docx", f)})

    resp = client.post("/ask", headers=headers, json={"question": "What does the indemnification clause say?"})
    assert resp.status_code == 503
