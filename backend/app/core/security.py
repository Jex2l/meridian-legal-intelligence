"""Minimal signed-token auth for the MVP: no passwords, just an email-based
login that issues an HMAC-signed token binding to a user id + expiry.

This is intentionally simple (no password hashing, no refresh tokens, no
revocation) -- fine for an MVP demo, NOT production-ready auth. The reason
it still matters here: it's what stops a client from picking its own
workspace_id on an API request. The server resolves workspace_id from the
verified token server-side; a request can never assert "I am workspace X."
"""

import base64
import hashlib
import hmac
import json
import time
import uuid

from app.core.config import settings


def _sign(payload: bytes) -> str:
    sig = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def issue_token(user_id: uuid.UUID) -> str:
    payload = json.dumps({"uid": str(user_id), "exp": int(time.time()) + settings.token_ttl_seconds}).encode()
    payload_b64 = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return f"{payload_b64}.{_sign(payload)}"


def verify_token(token: str) -> uuid.UUID | None:
    try:
        payload_b64, sig = token.split(".", 1)
        payload = base64.urlsafe_b64decode(payload_b64 + "==")
        expected_sig = _sign(payload)
        if not hmac.compare_digest(sig, expected_sig):
            return None
        data = json.loads(payload)
        if data["exp"] < time.time():
            return None
        return uuid.UUID(data["uid"])
    except (ValueError, KeyError, UnicodeDecodeError):
        return None
