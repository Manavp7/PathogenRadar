from fastapi import Depends, Header, HTTPException, status

from pathogenradar_api.core.config import Settings, get_settings
from pathogenradar_api.domain.models import Role


class Principal:
    def __init__(self, role: Role = Role.PUBLIC_CONSUMER, subject: str = "demo-user") -> None:
        self.role = role
        self.subject = subject


def get_principal(
    x_api_key: str | None = Header(default=None),
    x_role: Role | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if settings.require_api_key and x_api_key != settings.demo_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return Principal(role=x_role or Role.PUBLIC_CONSUMER)
