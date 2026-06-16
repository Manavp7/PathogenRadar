"""Audit-trail endpoint (admin-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..security.auth import recent_audit
from ..security.rbac import require_permission

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit", dependencies=[Depends(require_permission("admin"))])
def get_audit(limit: int = Query(default=200, ge=1, le=1000)) -> list[dict]:
    return recent_audit(limit)
