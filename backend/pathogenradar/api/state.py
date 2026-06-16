"""In-memory application state for the API, backed by persisted per-region pipeline artifacts.

Supports multiple regions simultaneously (e.g. Kerala + Tamil Nadu) and a national roll-up.
On first use, if the default region has no artifacts, the flagship scenario is generated.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import pandas as pd

from ..config import get_settings
from ..regions import available_regions, get_districts, region_geojson_path
from ..store import repo

logger = logging.getLogger("pathogenradar.api.state")


@dataclass
class RegionState:
    key: str
    meta: dict = field(default_factory=dict)
    risk_latest: list[dict] = field(default_factory=list)
    forecasts: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    risk_ts: pd.DataFrame = field(default_factory=pd.DataFrame)
    signal_scores: pd.DataFrame = field(default_factory=pd.DataFrame)
    signals: pd.DataFrame = field(default_factory=pd.DataFrame)
    _geojson: dict | None = None

    def geojson(self) -> dict:
        if self._geojson is None:
            with open(region_geojson_path(self.key), encoding="utf-8") as fh:
                self._geojson = json.load(fh)
        return self._geojson

    def districts(self) -> list[dict]:
        return [d.model_dump() for d in get_districts(self.key)]


class AppState:
    def __init__(self) -> None:
        self.regions: dict[str, RegionState] = {}

    @property
    def default_region(self) -> str:
        return get_settings().region

    def ensure_seed(self) -> None:
        default = self.default_region
        if not (repo.region_dir(default) / "risk_latest.json").exists():
            logger.info(
                "no artifacts for default region '%s' — generating golden scenario", default
            )
            from ..pipeline import golden_scenario

            golden_scenario(region=default)
        self.reload()

    def reload(self) -> None:
        self.regions = {}
        for r in available_regions():
            if (repo.region_dir(r) / "meta.json").exists():
                self.regions[r] = self._load_region(r)
        logger.info("loaded regions: %s", list(self.regions))

    def _load_region(self, r: str) -> RegionState:
        return RegionState(
            key=r,
            meta=repo.read_json("meta.json", {}, region=r) or {},
            risk_latest=repo.read_json("risk_latest.json", [], region=r) or [],
            forecasts=repo.read_json("forecasts.json", [], region=r) or [],
            alerts=repo.read_json(repo.ALERTS_JSON, [], region=r) or [],
            sources=repo.read_json("sources.json", {}, region=r) or {},
            risk_ts=repo.read_frame(repo.RISK_PARQUET, region=r),
            signal_scores=repo.read_frame("signal_scores.parquet", region=r),
            signals=repo.read_signals(region=r),
        )

    def available(self) -> list[str]:
        return list(self.regions.keys())

    def get(self, region: str | None = None) -> RegionState | None:
        return self.regions.get(region or self.default_region)


state = AppState()
