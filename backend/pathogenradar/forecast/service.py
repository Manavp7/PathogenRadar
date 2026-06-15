"""Forecast orchestration: derive current risk from assessments and project spread."""

from __future__ import annotations

from ..detection.engine import latest_by_district
from ..domain.models import DistrictForecast, RiskAssessment
from .deterministic import DEFAULT_HORIZONS, forecast_spread


def forecast_from_assessments(
    assessments: list[RiskAssessment],
    horizons: list[int] | None = None,
) -> list[DistrictForecast]:
    latest = latest_by_district(assessments)
    current_risk = {d: a.risk_score for d, a in latest.items()}
    return forecast_spread(current_risk, horizons or DEFAULT_HORIZONS)
