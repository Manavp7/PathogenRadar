"""Outbreak level classification from a 0..100 risk score."""

from __future__ import annotations

from ..domain.models import OutbreakLevel

# Lower bounds (inclusive) for each escalating level.
THRESHOLDS: list[tuple[float, OutbreakLevel]] = [
    (75.0, OutbreakLevel.EMERGENCY),
    (55.0, OutbreakLevel.ALERT),
    (35.0, OutbreakLevel.WARNING),
    (15.0, OutbreakLevel.WATCH),
    (0.0, OutbreakLevel.NORMAL),
]


def level_for(risk: float) -> OutbreakLevel:
    for lower, level in THRESHOLDS:
        if risk >= lower:
            return level
    return OutbreakLevel.NORMAL
