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


class FakeProvider(LLMProvider):
    """Deterministic stand-in used by tests and local dry-runs, so the
    generation/citation-validation/low-confidence logic can be exercised
    without network access or an API key."""

    def __init__(self, fixed_response: str):
        self._fixed_response = fixed_response

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        return self._fixed_response


def get_default_provider() -> LLMProvider:
    return AnthropicProvider()
