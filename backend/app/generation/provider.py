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


class GroqProvider(LLMProvider):
    """Groq's free-tier hosted inference API (OpenAI-compatible chat
    completions), for fast cloud generation with no self-hosted compute --
    the production default when no Anthropic key is configured, since
    Ollama isn't realistically runnable on a free hosting tier."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._api_key = api_key or settings.groq_api_key
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Set it in backend/.env to use Groq for generation.")
        self._model = model or settings.groq_model

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        import httpx

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Groq API timed out after 60s generating with '{self._model}'.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise RuntimeError("Groq API rejected the request: GROQ_API_KEY is invalid or expired.") from exc
            if exc.response.status_code == 429:
                raise RuntimeError("Groq API rate limit reached; try again shortly.") from exc
            raise RuntimeError(f"Groq API returned an error: {exc}") from exc

        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Groq API returned an unexpected response shape: {response.text[:200]}") from exc


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
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama at {self._base_url} timed out after 120s generating with '{self._model}'. "
                "The model may be too large for this machine, or another request is already running."
            ) from exc
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self._base_url}. Run `ollama serve` "
                f"(and `ollama pull {self._model}`) or set ANTHROPIC_API_KEY instead."
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise RuntimeError(
                    f"Ollama doesn't have model '{self._model}' pulled. Run `ollama pull {self._model}`."
                ) from exc
            raise RuntimeError(f"Ollama returned an error: {exc}") from exc

        try:
            return response.json()["message"]["content"]
        except (ValueError, KeyError) as exc:
            raise RuntimeError(f"Ollama returned an unexpected response shape: {response.text[:200]}") from exc


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
    """Anthropic if a key is configured (best quality, paid); otherwise
    Groq if a key is configured (free-tier cloud inference, no self-hosted
    compute needed -- the practical default for a free-tier deployment);
    otherwise a local Ollama model if one is reachable (zero cloud
    dependency, for local dev). Raises a clear error only if none are
    available."""
    if settings.anthropic_api_key:
        return AnthropicProvider()
    if settings.groq_api_key:
        return GroqProvider()
    if _ollama_reachable():
        return OllamaProvider()
    raise RuntimeError(
        "No LLM provider available: ANTHROPIC_API_KEY and GROQ_API_KEY are both "
        f"unset, and Ollama is not reachable at {settings.ollama_base_url}. Set "
        "one of the two API keys in backend/.env, or run `ollama serve`."
    )
