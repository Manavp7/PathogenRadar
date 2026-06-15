"""Alert endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from .state import state

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def get_alerts() -> list[dict]:
    return state.alerts
