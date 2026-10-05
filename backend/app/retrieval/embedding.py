"""Dense embeddings, behind a swappable provider -- same pattern as
app/generation/provider.py.

"local" (default) loads sentence-transformers in-process. That needs
torch, which combined with the reranker's cross-encoder model was
confirmed live to exceed a 512MB host's RAM during startup. "huggingface_api"
calls HF's hosted inference API instead, so the backend never needs torch
installed at all -- used in production (see render.yaml / docs/DEPLOYMENT.md).
"""

from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingProvider(EmbeddingProvider):
    @lru_cache(maxsize=1)
    def _model(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.embedding_model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vectors]


class HuggingFaceApiEmbeddingProvider(EmbeddingProvider):
    """Calls HF's router-based Inference API feature-extraction endpoint.
    Requires a personal access token with "Inference Providers" permission
    (create one at huggingface.co/settings/tokens)."""

    def __init__(self, model: str | None = None, api_token: str | None = None):
        self._model_id = (model or settings.embedding_model).removeprefix("sentence-transformers/")
        self._api_token = api_token or settings.hf_api_token
        if not self._api_token:
            raise RuntimeError("HF_API_TOKEN is not set. Set it in backend/.env to use the HuggingFace embedding provider.")

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx

        url = f"https://router.huggingface.co/hf-inference/models/sentence-transformers/{self._model_id}/pipeline/feature-extraction"
        try:
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {self._api_token}"},
                json={"inputs": texts, "normalize": True},
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError("HuggingFace Inference API timed out after 60s generating embeddings.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise RuntimeError("HF_API_TOKEN is invalid or lacks Inference Providers permission.") from exc
            raise RuntimeError(f"HuggingFace Inference API returned an error: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(f"HuggingFace Inference API returned an unexpected response: {response.text[:200]}") from exc


@lru_cache(maxsize=1)
def _provider() -> EmbeddingProvider:
    if settings.embedding_provider == "huggingface_api":
        return HuggingFaceApiEmbeddingProvider()
    return LocalEmbeddingProvider()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _provider().embed(texts)


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
