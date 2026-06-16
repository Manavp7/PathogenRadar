"""Role-based access control.

Roles map to permission sets. When no API keys are configured the API runs in open dev mode
(treated as admin). When keys are configured, each request must present a valid ``X-API-Key``
whose role grants the required permission, else 401/403.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fastapi import Header, HTTPException, status

from ..config import get_settings


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    MINISTER = "minister"
    ADMIN = "admin"


# Permissions: read (dashboards), simulate (run models), admin (audit/MLOps/system writes).
ROLE_PERMS: dict[str, set[str]] = {
    Role.VIEWER.value: {"read"},
    Role.MINISTER.value: {"read"},
    Role.ANALYST.value: {"read", "simulate"},
    Role.ADMIN.value: {"read", "simulate", "admin"},
}


@dataclass
class Principal:
    role: str
    key_id: str
    authenticated: bool


def _mask(key: str) -> str:
    return f"{key[:3]}…{key[-2:]}" if len(key) > 6 else "key"


def resolve_principal(x_api_key: str | None) -> Principal | None:
    settings = get_settings()
    key_map = settings.api_key_map()
    if not key_map:
        return Principal(role=Role.ADMIN.value, key_id="dev", authenticated=False)  # open dev mode
    if x_api_key and x_api_key in key_map:
        return Principal(role=key_map[x_api_key], key_id=_mask(x_api_key), authenticated=True)
    return None


def has_permission(role: str, perm: str) -> bool:
    return perm in ROLE_PERMS.get(role, set())


def require_permission(perm: str):
    """Dependency factory enforcing a permission for a route."""

    async def _dep(x_api_key: str | None = Header(default=None)) -> Principal:
        principal = resolve_principal(x_api_key)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key"
            )
        if not has_permission(principal.role, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{principal.role}' lacks permission '{perm}'",
            )
        return principal

    return _dep
