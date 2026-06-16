"""Alert endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from .deps import region_state
from .pagination import paginate
from .state import RegionState

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def get_alerts(
    limit: int | None = Query(default=None, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    rs: RegionState = Depends(region_state),
) -> list[dict]:
    return paginate(rs.alerts, limit, offset)
