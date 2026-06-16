"""Briefing / report endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from ..domain.models import Briefing
from ..llm.briefing import generate_briefing
from .deps import region_state
from .state import RegionState

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/briefing", response_model=Briefing)
def get_briefing(rs: RegionState = Depends(region_state)) -> Briefing:
    region = rs.meta.get("region", "Kerala")
    as_of_raw = rs.meta.get("as_of")
    as_of = date.fromisoformat(as_of_raw) if as_of_raw else date.today()
    return generate_briefing(
        region=region,
        as_of=as_of,
        risk_latest=rs.risk_latest,
        forecasts=rs.forecasts,
        source_summary=rs.meta.get("source_summary", {}),
    )
