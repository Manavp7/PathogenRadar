"""System status endpoint: connectors, LLM provider, security, data freshness, config warnings."""

from __future__ import annotations

from fastapi import APIRouter

from .. import __version__
from ..config import get_settings
from ..forecast.service import active_model
from .state import state

router = APIRouter(prefix="/api", tags=["system"])


def _rl_threshold():
    try:
        from ..rl.agent import load_alert_threshold

        return load_alert_threshold()
    except Exception:  # noqa: BLE001
        return None


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
            "abdm_fhir": {"enabled": bool(s.fhir_base_url), "live": bool(s.fhir_base_url)},
        },
        "llm": {
            "provider": s.llm_provider,
            "key_present": s.llm_key_present(),
            "required": False,
        },
        "forecast_model": active_model(),
        "alerting": {
            "policy": s.alerting_policy,
            "rl_alert_threshold": _rl_threshold(),
        },
        "security": {"api_key_required": bool(s.api_key)},
        "regions": state.available(),
        "default_region": state.default_region,
        "warnings": s.warnings(),
    }
