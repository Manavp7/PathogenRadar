"""Named outbreak scenarios for seeding and demos.

Each scenario returns the outbreak events to inject. Scenarios are tuned to peak near "now"
so the dashboard reads as an active situation. ``multi`` runs three different-category
outbreaks at once to demonstrate the classifier/knowledge-graph generalising.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

from .acquisition.synthetic import (
    OutbreakEvent,
    dengue_outbreak,
    respiratory_outbreak,
    waterborne_outbreak,
)
from .pipeline import PipelineResult, run_pipeline

# Sharp, recent outbreak shape so the latest day reads as active.
_RECENT_OFFSET = 14
_DURATION = 32
_PEAK = 12


def _dengue(as_of: date) -> list[OutbreakEvent]:
    return [
        dengue_outbreak("ernakulam", as_of - timedelta(days=_RECENT_OFFSET), 2.4, _DURATION, _PEAK)
    ]


def _respiratory(as_of: date) -> list[OutbreakEvent]:
    return [
        respiratory_outbreak(
            "thiruvananthapuram", as_of - timedelta(days=_RECENT_OFFSET), 2.2, _DURATION, _PEAK
        )
    ]


def _waterborne(as_of: date) -> list[OutbreakEvent]:
    return [
        waterborne_outbreak(
            "kozhikode", as_of - timedelta(days=_RECENT_OFFSET), 2.3, _DURATION, _PEAK
        )
    ]


def _multi(as_of: date) -> list[OutbreakEvent]:
    return _dengue(as_of) + _respiratory(as_of) + _waterborne(as_of)


SCENARIOS: dict[str, Callable[[date], list[OutbreakEvent]]] = {
    "dengue": _dengue,
    "respiratory": _respiratory,
    "waterborne": _waterborne,
    "multi": _multi,
}


def run_scenario(
    name: str = "multi",
    as_of: date | None = None,
    persist: bool = True,
) -> PipelineResult:
    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario '{name}'. Options: {', '.join(SCENARIOS)}")
    end = as_of or date.today()
    start = end - timedelta(days=180)
    outbreaks = SCENARIOS[name](end)
    return run_pipeline(start, end, outbreaks=outbreaks, persist=persist)
