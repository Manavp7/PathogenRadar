"""Lightweight security: optional API-key auth and an audit log.

Full RBAC / ABDM / HIPAA controls are a later phase. By default (no key configured) the API
runs open for local development; setting ``PATHOGENRADAR_API_KEY`` enforces the header.
"""

from __future__ import annotations

import logging

from fastapi import Header, HTTPException, status

from ..config import get_settings

audit_logger = logging.getLogger("pathogenradar.audit")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency enforcing the API key when one is configured."""
    settings = get_settings()
    if not settings.api_key:
        return  # open dev mode
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
