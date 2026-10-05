import pytest

from app.retrieval import embedding as embedding_module
from app.retrieval.embedding import HuggingFaceApiEmbeddingProvider, LocalEmbeddingProvider, _provider


def test_provider_selects_local_by_default(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "local")
    _provider.cache_clear()
    result = _provider()
    assert isinstance(result, LocalEmbeddingProvider)
    _provider.cache_clear()


def test_provider_selects_huggingface_api_when_configured(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "huggingface_api")
    monkeypatch.setattr(embedding_module.settings, "hf_api_token", "fake-token")
    _provider.cache_clear()
    result = _provider()
    assert isinstance(result, HuggingFaceApiEmbeddingProvider)
    _provider.cache_clear()
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "local")


def test_hf_provider_requires_api_token(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "hf_api_token", "")
    with pytest.raises(RuntimeError, match="HF_API_TOKEN is not set"):
        HuggingFaceApiEmbeddingProvider()


def test_hf_provider_embed_parses_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    def fake_post(url, headers, json, timeout):
        assert url == "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
        assert headers["Authorization"] == "Bearer test-token"
        assert json["inputs"] == ["a", "b"]
        assert json["normalize"] is True
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = HuggingFaceApiEmbeddingProvider(model="sentence-transformers/all-MiniLM-L6-v2", api_token="test-token")
    result = provider.embed(["a", "b"])
    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_hf_provider_raises_clear_error_on_invalid_token(monkeypatch):
    import httpx

    class FakeResponse:
        status_code = 401

        def raise_for_status(self):
            raise httpx.HTTPStatusError("unauthorized", request=None, response=self)

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = HuggingFaceApiEmbeddingProvider(api_token="bad-token")
    with pytest.raises(RuntimeError, match="HF_API_TOKEN is invalid"):
        provider.embed(["a"])
