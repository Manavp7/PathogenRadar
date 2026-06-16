"""Forecast orchestration: derive current risk from assessments and project spread.

Chooses the forecasting model via ``FORECAST_MODEL`` (deterministic | gnn). The GNN is used
only when PyTorch and a trained model are present; otherwise we fall back to the deterministic
gravity-diffusion model so the platform always produces a forecast.
"""

from __future__ import annotations

import logging
import os

from ..detection.engine import latest_by_district
from ..domain.models import DistrictForecast, RiskAssessment
from .deterministic import DEFAULT_HORIZONS, forecast_spread

logger = logging.getLogger("pathogenradar.forecast")


def active_model() -> str:
    """Return the forecast model actually in use ('gnn' or 'deterministic')."""
    requested = os.getenv("FORECAST_MODEL", "deterministic").lower()
    if requested == "gnn":
        from .gnn import gnn_available

        if gnn_available():
            return "gnn"
        logger.info("FORECAST_MODEL=gnn requested but unavailable — using deterministic")
    return "deterministic"


def forecast_current(
    current_risk: dict[str, float],
    horizons: list[int] | None = None,
) -> list[DistrictForecast]:
    horizons = horizons or DEFAULT_HORIZONS
    if active_model() == "gnn":
        try:
            from .gnn import forecast_spread_gnn

            return forecast_spread_gnn(current_risk, horizons)
        except Exception as exc:  # noqa: BLE001 - never fail a forecast
            logger.warning("GNN forecast failed (%s) — falling back to deterministic", exc)
    return forecast_spread(current_risk, horizons)


def forecast_from_assessments(
    assessments: list[RiskAssessment],
    horizons: list[int] | None = None,
) -> list[DistrictForecast]:
    latest = latest_by_district(assessments)
    current_risk = {d: a.risk_score for d, a in latest.items()}
    return forecast_current(current_risk, horizons or DEFAULT_HORIZONS)
