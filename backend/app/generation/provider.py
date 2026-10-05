"""Thin provider interface so the LLM backing generation can be swapped
without touching the rest of the generation package.
"""

from abc import ABC, abstractmethod

from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None):
        import anthropic

        key = api_key or settings.anthropic_api_key
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it in backend/.env to use generation/drafting."
            )
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class OllamaProvider(LLMProvider):
    """Local-model fallback via Ollama's REST API. No API key needed, runs
    entirely on this machine -- useful for development/demo when no
    Anthropic key is configured, and a reasonable production choice for a
    firm that wants generation to never leave its own infrastructure."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        import httpx

        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
                timeout=120.0,
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self._base_url}. Run `ollama serve` "
                f"(and `ollama pull {self._model}`) or set ANTHROPIC_API_KEY instead."
            ) from exc
        return response.json()["message"]["content"]


class FakeProvider(LLMProvider):
    """Deterministic stand-in used by tests and local dry-runs, so the
    generation/citation-validation/low-confidence logic can be exercised
    without network access or an API key."""

    def __init__(self, fixed_response: str):
        self._fixed_response = fixed_response

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        return self._fixed_response


def _ollama_reachable() -> bool:
    import httpx

    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=1.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def get_default_provider() -> LLMProvider:
    """Anthropic if a key is configured (best quality); otherwise fall back
    to a local Ollama model if one is reachable, so the app still works
    with zero cloud dependency. Raises a clear error only if neither is
    available."""
    if settings.anthropic_api_key:
        return AnthropicProvider()
    if _ollama_reachable():
        return OllamaProvider()
    raise RuntimeError(
        "No LLM provider available: ANTHROPIC_API_KEY is not set, and "
        f"Ollama is not reachable at {settings.ollama_base_url}. Set "
        "ANTHROPIC_API_KEY in backend/.env, or run `ollama serve`."
    )
