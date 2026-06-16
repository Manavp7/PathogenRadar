"""Reference endpoints: regions, districts, geo, metadata, source reliability."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .deps import region_state
from .state import RegionState, state

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/regions")
def get_regions() -> dict:
    return {
        "default": state.default_region,
        "regions": [
            {"key": k, "name": rs.meta.get("region", k), "districts": len(rs.districts())}
            for k, rs in state.regions.items()
        ],
    }


@router.get("/meta")
def get_meta(rs: RegionState = Depends(region_state)) -> dict:
    return {
        **rs.meta,
        "districts": len(rs.districts()),
        "active_alerts": len(rs.alerts),
    }


@router.get("/districts")
def get_districts_route(rs: RegionState = Depends(region_state)) -> list[dict]:
    return rs.districts()


@router.get("/geojson")
def get_geojson(rs: RegionState = Depends(region_state)) -> dict:
    return rs.geojson()


@router.get("/sources")
def get_sources(rs: RegionState = Depends(region_state)) -> dict:
    return rs.sources
