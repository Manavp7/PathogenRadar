"""Briefing / report endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from ..domain.models import Briefing
from ..llm.briefing import generate_briefing
from .state import state

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/briefing", response_model=Briefing)
def get_briefing() -> Briefing:
    region = state.meta.get("region", "Kerala")
    as_of_raw = state.meta.get("as_of")
    as_of = date.fromisoformat(as_of_raw) if as_of_raw else date.today()
    return generate_briefing(
        region=region,
        as_of=as_of,
        risk_latest=state.risk_latest,
        forecasts=state.forecasts,
        source_summary=state.meta.get("source_summary", {}),
    )
