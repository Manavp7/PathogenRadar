"""Central configuration for PathogenRadar.

Everything is optional and has safe offline defaults. Reads environment variables (and a
local ``.env`` if present) plus the region definition file. No external services are required.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Repo root = three levels up from this file: backend/pathogenradar/config.py -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = DATA_DIR / "config"
GEO_DIR = DATA_DIR / "geo"
CACHE_DIR = DATA_DIR / "cache"
SEED_DIR = DATA_DIR / "seed"

# Load .env if present (never required).
load_dotenv(REPO_ROOT / ".env")


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings resolved from the environment with offline-safe defaults."""

    region: str = field(default_factory=lambda: os.getenv("PATHOGENRADAR_REGION", "kerala"))

    # Optional real connectors. Default: fully offline (synthetic/cached).
    openweather_api_key: str | None = field(
        default_factory=lambda: os.getenv("OPENWEATHER_API_KEY") or None
    )
    enable_google_trends: bool = field(
        default_factory=lambda: _get_bool("ENABLE_GOOGLE_TRENDS", False)
    )

    # Optional LLM provider. Default: template (no AI, no network).
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "template"))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY") or None)
    anthropic_api_key: str | None = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY") or None
    )
    gemini_api_key: str | None = field(default_factory=lambda: os.getenv("GEMINI_API_KEY") or None)
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # Optional API security. If unset, the API runs open (dev mode).
    api_key: str | None = field(default_factory=lambda: os.getenv("PATHOGENRADAR_API_KEY") or None)

    @property
    def region_config_path(self) -> Path:
        return CONFIG_DIR / "regions.yaml"

    @property
    def geojson_path(self) -> Path:
        return GEO_DIR / f"{self.region}_districts.geojson"

    @property
    def offline_mode(self) -> bool:
        """True when no external services are configured (the default state)."""
        return not (self.openweather_api_key or self.enable_google_trends)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def load_region_config() -> dict:
    """Load the region definition (districts, populations, adjacency, coordinates)."""
    settings = get_settings()
    path = settings.region_config_path
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if settings.region not in data:
        raise KeyError(f"Region '{settings.region}' not found in {path}")
    return data[settings.region]


def ensure_dirs() -> None:
    for d in (DATA_DIR, CONFIG_DIR, GEO_DIR, CACHE_DIR, SEED_DIR):
        d.mkdir(parents=True, exist_ok=True)
