"""Alert endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .pagination import paginate
from .state import state

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def get_alerts(
    limit: int | None = Query(default=None, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    return paginate(state.alerts, limit, offset)
