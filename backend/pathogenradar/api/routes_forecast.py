"""Spread-forecast endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from .deps import region_state
from .pagination import paginate
from .state import RegionState

router = APIRouter(prefix="/api", tags=["forecast"])


@router.get("/forecast")
def get_forecast(
    limit: int | None = Query(default=None, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    rs: RegionState = Depends(region_state),
) -> list[dict]:
    return paginate(rs.forecasts, limit, offset)


@router.get("/forecast/{district_id}")
def get_forecast_for_district(district_id: str, rs: RegionState = Depends(region_state)) -> dict:
    f = next((x for x in rs.forecasts if x["district_id"] == district_id), None)
    if f is None:
        raise HTTPException(status_code=404, detail=f"No forecast for district '{district_id}'")
    return f
