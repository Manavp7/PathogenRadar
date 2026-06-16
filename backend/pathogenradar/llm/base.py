"""LLM briefing provider interface.

The platform NEVER requires an LLM. Briefings are produced by the deterministic
``TemplateBriefingProvider`` by default; optional cloud/local providers (OpenAI, Anthropic,
Gemini, Ollama) can polish the prose when explicitly configured, and always fall back to the
template if unavailable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class BriefingContext:
    """Structured, model-ready summary of the current situation."""

    region: str
    as_of: date
    total_districts: int
    districts_on_alert: int
    top_districts: list[dict] = field(
        default_factory=list
    )  # {name, risk, level, category, diseases}
    forecast_highlights: list[dict] = field(default_factory=list)  # {name, prob_30d}
    recommended_actions: list[str] = field(default_factory=list)
    data_sources: dict[str, str] = field(default_factory=dict)


class BriefingProvider(ABC):
    name: str = "base"

    @property
    def available(self) -> bool:
        return True

    @abstractmethod
    def render(self, context: BriefingContext) -> str:
        """Return the briefing body (Markdown)."""
