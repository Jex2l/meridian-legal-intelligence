import pytest

from app.retrieval import embedding as embedding_module
from app.retrieval.embedding import (
    CohereEmbeddingProvider,
    HuggingFaceApiEmbeddingProvider,
    LocalEmbeddingProvider,
    _provider,
)


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


def test_hf_provider_raises_clear_error_on_payment_required(monkeypatch):
    import httpx

    class FakeResponse:
        status_code = 402

        def raise_for_status(self):
            raise httpx.HTTPStatusError("payment required", request=None, response=self)

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = HuggingFaceApiEmbeddingProvider(api_token="test-token")
    with pytest.raises(RuntimeError, match="paid/credited account"):
        provider.embed(["a"])


def test_provider_selects_cohere_when_configured(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "cohere")
    monkeypatch.setattr(embedding_module.settings, "cohere_api_key", "fake-key")
    _provider.cache_clear()
    result = _provider()
    assert isinstance(result, CohereEmbeddingProvider)
    _provider.cache_clear()
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "local")


def test_cohere_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "cohere_api_key", "")
    with pytest.raises(RuntimeError, match="COHERE_API_KEY is not set"):
        CohereEmbeddingProvider()


def test_cohere_provider_embed_parses_response_and_sets_input_type(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": {"float": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]}}

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        assert headers["Authorization"] == "Bearer test-key"
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = CohereEmbeddingProvider(model="embed-english-light-v3.0", api_key="test-key")

    doc_result = provider.embed(["a", "b"], is_query=False)
    assert doc_result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    assert captured["url"] == "https://api.cohere.com/v2/embed"
    assert captured["json"]["input_type"] == "search_document"

    provider.embed(["a"], is_query=True)
    assert captured["json"]["input_type"] == "search_query"


def test_cohere_provider_raises_clear_error_on_invalid_key(monkeypatch):
    import httpx

    class FakeResponse:
        status_code = 401

        def raise_for_status(self):
            raise httpx.HTTPStatusError("unauthorized", request=None, response=self)

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = CohereEmbeddingProvider(api_key="bad-key")
    with pytest.raises(RuntimeError, match="COHERE_API_KEY is invalid"):
        provider.embed(["a"])


def test_embed_query_uses_search_query_input_type(monkeypatch):
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "cohere")
    monkeypatch.setattr(embedding_module.settings, "cohere_api_key", "fake-key")
    embedding_module._provider.cache_clear()

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": {"float": [[0.1, 0.2]]}}

    def fake_post(url, headers, json, timeout):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    vector = embedding_module.embed_query("what is the indemnity clause")
    assert vector == [0.1, 0.2]
    assert captured["json"]["input_type"] == "search_query"

    embedding_module._provider.cache_clear()
    monkeypatch.setattr(embedding_module.settings, "embedding_provider", "local")
