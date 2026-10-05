import pytest

from app.generation import provider as provider_module
from app.generation.provider import OllamaProvider, get_default_provider


def test_get_default_provider_prefers_anthropic_when_key_set(monkeypatch):
    monkeypatch.setattr(provider_module.settings, "anthropic_api_key", "fake-key")
    called = {}

    class FakeAnthropicProvider:
        def __init__(self):
            called["anthropic"] = True

    monkeypatch.setattr(provider_module, "AnthropicProvider", FakeAnthropicProvider)
    get_default_provider()
    assert called.get("anthropic") is True


def test_get_default_provider_falls_back_to_ollama_when_reachable(monkeypatch):
    monkeypatch.setattr(provider_module.settings, "anthropic_api_key", "")
    monkeypatch.setattr(provider_module, "_ollama_reachable", lambda: True)
    result = get_default_provider()
    assert isinstance(result, OllamaProvider)


def test_get_default_provider_raises_clear_error_when_nothing_available(monkeypatch):
    monkeypatch.setattr(provider_module.settings, "anthropic_api_key", "")
    monkeypatch.setattr(provider_module, "_ollama_reachable", lambda: False)
    with pytest.raises(RuntimeError, match="No LLM provider available"):
        get_default_provider()


def test_ollama_provider_generate_parses_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "hello [1]"}}

    def fake_post(url, json, timeout):
        assert url.endswith("/api/chat")
        assert json["model"] == "qwen2.5:7b"
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    result = OllamaProvider(model="qwen2.5:7b").generate("system", "user")
    assert result == "hello [1]"


def test_ollama_provider_raises_clear_error_when_unreachable(monkeypatch):
    import httpx

    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr("httpx.post", fake_post)
    with pytest.raises(RuntimeError, match="Could not reach Ollama"):
        OllamaProvider().generate("system", "user")
