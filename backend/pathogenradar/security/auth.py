"""Authentication + audit primitives.

``require_api_key`` enforces the "read" permission (the baseline for all data routes). Higher
permissions are enforced per-route via :func:`pathogenradar.security.rbac.require_permission`.
By default (no keys configured) the API runs open for local development.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import UTC, datetime

from .rbac import require_permission

audit_logger = logging.getLogger("pathogenradar.audit")

# Baseline gate for all data routers.
require_api_key = require_permission("read")

# In-memory audit trail (most recent first via reversed access).
_AUDIT: deque[dict] = deque(maxlen=1000)


def record_audit(
    method: str, path: str, status_code: int, role: str, key_id: str, ms: float
) -> None:
    _AUDIT.append(
        {
            "ts": datetime.now(UTC).isoformat(timespec="seconds"),
            "method": method,
            "path": path,
            "status": status_code,
            "role": role,
            "principal": key_id,
            "ms": round(ms, 1),
        }
    )


def recent_audit(limit: int = 200) -> list[dict]:
    return list(reversed(_AUDIT))[:limit]
