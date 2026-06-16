"""LLM briefing package. The platform runs fully offline; LLM providers are optional."""

from __future__ import annotations

from ..config import get_settings
from .base import BriefingContext, BriefingProvider
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)
from .template import TemplateBriefingProvider

__all__ = [
    "BriefingContext",
    "BriefingProvider",
    "TemplateBriefingProvider",
    "get_briefing_provider",
]

_PROVIDERS: dict[str, type[BriefingProvider]] = {
    "template": TemplateBriefingProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_briefing_provider() -> BriefingProvider:
    """Return the configured provider. Defaults to the offline template provider."""
    name = (get_settings().llm_provider or "template").lower()
    provider_cls = _PROVIDERS.get(name, TemplateBriefingProvider)
    return provider_cls()
