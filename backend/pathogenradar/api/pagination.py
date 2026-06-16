"""Optional offset/limit pagination for list endpoints.

Defaults preserve "return everything" so existing clients (and the dashboard) are unaffected.
"""

from __future__ import annotations


def paginate(items: list, limit: int | None, offset: int = 0) -> list:
    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]
    return items
