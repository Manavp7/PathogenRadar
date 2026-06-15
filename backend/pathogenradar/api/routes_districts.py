"""Reference endpoints: districts, geo, metadata, source reliability."""

from __future__ import annotations

from fastapi import APIRouter

from .state import state

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/meta")
def get_meta() -> dict:
    return {
        **state.meta,
        "districts": len(state.districts()),
        "active_alerts": len(state.alerts),
    }


@router.get("/districts")
def get_districts_route() -> list[dict]:
    return state.districts()


@router.get("/geojson")
def get_geojson() -> dict:
    return state.geojson()


@router.get("/sources")
def get_sources() -> dict:
    return state.sources
