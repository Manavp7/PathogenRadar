"""System status endpoint: connectors, LLM provider, security, data freshness, config warnings."""

from __future__ import annotations

from fastapi import APIRouter

from .. import __version__
from ..config import get_settings
from .state import state

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system")
def get_system() -> dict:
    s = get_settings()
    return {
        "version": __version__,
        "region": s.region,
        "offline_mode": s.offline_mode,
        "connectors": {
            "synthetic": {"enabled": True, "live": False},
            "google_trends": {"enabled": s.enable_google_trends, "live": s.enable_google_trends},
            "openweather": {
                "enabled": bool(s.openweather_api_key),
                "live": bool(s.openweather_api_key),
            },
        },
        "llm": {
            "provider": s.llm_provider,
            "key_present": s.llm_key_present(),
            "required": False,
        },
        "security": {"api_key_required": bool(s.api_key)},
        "data": {
            "as_of": state.meta.get("as_of"),
            "source_summary": state.meta.get("source_summary", {}),
        },
        "warnings": s.warnings(),
    }
