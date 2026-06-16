"""Shared API dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Query

from .state import RegionState, state


def region_state(region: str | None = Query(default=None, description="Region key")) -> RegionState:
    rs = state.get(region)
    if rs is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region or state.default_region}' not loaded. "
            f"Available: {', '.join(state.available()) or 'none'}",
        )
    return rs
