"""Named outbreak scenarios for seeding and demos (region-aware).

Each scenario returns the outbreak events to inject, choosing districts per region (named
anchors for Kerala, population rank otherwise). ``multi`` runs three different-category
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
from .regions import get_districts

# Sharp, recent outbreak shape so the latest day reads as active.
_RECENT_OFFSET = 14
_DURATION = 32
_PEAK = 12

_ANCHORS = {
    "kerala": {
        "dengue": "ernakulam",
        "respiratory": "thiruvananthapuram",
        "waterborne": "kozhikode",
    }
}


def scenario_district(region: str, kind: str, rank: int) -> str:
    """The district to seed for a scenario kind: named anchor if defined, else by population."""
    anchor = _ANCHORS.get(region, {}).get(kind)
    if anchor:
        return anchor
    ranked = sorted(get_districts(region), key=lambda d: d.population, reverse=True)
    return ranked[min(rank, len(ranked) - 1)].id


def _dengue(as_of: date, region: str) -> list[OutbreakEvent]:
    d = scenario_district(region, "dengue", 0)
    return [dengue_outbreak(d, as_of - timedelta(days=_RECENT_OFFSET), 2.4, _DURATION, _PEAK)]


def _respiratory(as_of: date, region: str) -> list[OutbreakEvent]:
    d = scenario_district(region, "respiratory", 1)
    return [respiratory_outbreak(d, as_of - timedelta(days=_RECENT_OFFSET), 2.2, _DURATION, _PEAK)]


def _waterborne(as_of: date, region: str) -> list[OutbreakEvent]:
    d = scenario_district(region, "waterborne", 2)
    return [waterborne_outbreak(d, as_of - timedelta(days=_RECENT_OFFSET), 2.3, _DURATION, _PEAK)]


def _multi(as_of: date, region: str) -> list[OutbreakEvent]:
    return _dengue(as_of, region) + _respiratory(as_of, region) + _waterborne(as_of, region)


SCENARIOS: dict[str, Callable[[date, str], list[OutbreakEvent]]] = {
    "dengue": _dengue,
    "respiratory": _respiratory,
    "waterborne": _waterborne,
    "multi": _multi,
}


def run_scenario(
    name: str = "multi",
    as_of: date | None = None,
    persist: bool = True,
    region: str | None = None,
) -> PipelineResult:
    from .config import get_settings

    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario '{name}'. Options: {', '.join(SCENARIOS)}")
    region = region or get_settings().region
    end = as_of or date.today()
    start = end - timedelta(days=180)
    outbreaks = SCENARIOS[name](end, region)
    return run_pipeline(start, end, outbreaks=outbreaks, persist=persist, region=region)
