from datetime import UTC, datetime
from typing import Any


class AuditLogger:
    """In-memory audit scaffold for demo mode."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, actor: str, action: str, scope: str, metadata: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "actor": actor,
                "action": action,
                "scope": scope,
                "metadata": metadata or {},
            }
        )

    def list_events(self) -> list[dict[str, Any]]:
        return list(self.events)
