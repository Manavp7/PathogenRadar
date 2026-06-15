"""Spread-forecast endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .state import state

router = APIRouter(prefix="/api", tags=["forecast"])


@router.get("/forecast")
def get_forecast() -> list[dict]:
    return state.forecasts


@router.get("/forecast/{district_id}")
def get_forecast_for_district(district_id: str) -> dict:
    f = next((x for x in state.forecasts if x["district_id"] == district_id), None)
    if f is None:
        raise HTTPException(status_code=404, detail=f"No forecast for district '{district_id}'")
    return f
