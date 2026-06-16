"""Optional LLM briefing providers (OpenAI, Anthropic, Gemini, Ollama).

Each provider grounds the model on the deterministic template draft and asks only for prose
polishing — the LLM never makes predictions. Any failure (missing key, network, error)
transparently falls back to the template, so the platform always produces a briefing.
"""

from __future__ import annotations

import logging

from ..config import get_settings
from .base import BriefingContext, BriefingProvider
from .template import TemplateBriefingProvider

logger = logging.getLogger("pathogenradar.llm")

SYSTEM_PROMPT = (
    "You are a public-health communications assistant. Rewrite the provided disease-surveillance "
    "briefing into a crisp, professional one-page briefing for a state Health Minister. Use ONLY "
    "the facts given — do not invent numbers, predictions, or districts. Keep Markdown structure."
)


def _build_prompt(context: BriefingContext) -> str:
    draft = TemplateBriefingProvider().render(context)
    return f"Here is the factual briefing draft to refine:\n\n{draft}"


class _FallbackMixin(BriefingProvider):
    def render(self, context: BriefingContext) -> str:
        if not self.available:
            logger.info("%s provider unavailable — using template briefing", self.name)
            return TemplateBriefingProvider().render(context)
        try:
            return self._render_llm(context)
        except Exception as exc:  # noqa: BLE001 - never fail a briefing
            logger.warning("%s provider failed (%s) — using template briefing", self.name, exc)
            return TemplateBriefingProvider().render(context)

    def _render_llm(self, context: BriefingContext) -> str:  # pragma: no cover - needs network
        raise NotImplementedError


class OpenAIProvider(_FallbackMixin):
    name = "openai"

    @property
    def available(self) -> bool:
        return bool(get_settings().openai_api_key)

    def _render_llm(self, context: BriefingContext) -> str:  # pragma: no cover - needs network
        import requests

        key = get_settings().openai_api_key
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(context)},
                ],
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class AnthropicProvider(_FallbackMixin):
    name = "anthropic"

    @property
    def available(self) -> bool:
        return bool(get_settings().anthropic_api_key)

    def _render_llm(self, context: BriefingContext) -> str:  # pragma: no cover - needs network
        import requests

        key = get_settings().anthropic_api_key
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 1200,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": _build_prompt(context)}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


class GeminiProvider(_FallbackMixin):
    name = "gemini"

    @property
    def available(self) -> bool:
        return bool(get_settings().gemini_api_key)

    def _render_llm(self, context: BriefingContext) -> str:  # pragma: no cover - needs network
        import requests

        key = get_settings().gemini_api_key
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={key}"
        )
        resp = requests.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": _build_prompt(context)}]}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


class OllamaProvider(_FallbackMixin):
    name = "ollama"

    @property
    def available(self) -> bool:
        return True  # assume a local daemon may be present; falls back on connection error

    def _render_llm(self, context: BriefingContext) -> str:  # pragma: no cover - needs network
        import requests

        base = get_settings().ollama_base_url
        resp = requests.post(
            f"{base}/api/generate",
            json={
                "model": "llama3",
                "system": SYSTEM_PROMPT,
                "prompt": _build_prompt(context),
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["response"]
