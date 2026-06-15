"""In-memory application state for the API, backed by persisted pipeline artifacts.

On first use, if no artifacts exist, the flagship dengue scenario is generated so the
dashboard always has a meaningful story to show.
"""

from __future__ import annotations

import json
import logging

import pandas as pd

from ..config import get_settings
from ..regions import get_districts
from ..store import repo

logger = logging.getLogger("pathogenradar.api.state")


class AppState:
    def __init__(self) -> None:
        self.meta: dict = {}
        self.risk_latest: list[dict] = []
        self.forecasts: list[dict] = []
        self.alerts: list[dict] = []
        self.sources: dict = {}
        self.risk_ts: pd.DataFrame = pd.DataFrame()
        self.signal_scores: pd.DataFrame = pd.DataFrame()
        self.signals: pd.DataFrame = pd.DataFrame()
        self._geojson: dict | None = None

    def ensure_seed(self) -> None:
        if not (repo.SEED_DIR / "risk_latest.json").exists():
            logger.info("no pipeline artifacts found — generating golden dengue scenario")
            from ..pipeline import golden_scenario

            golden_scenario()
        self.reload()

    def reload(self) -> None:
        self.meta = repo.read_json("meta.json", {}) or {}
        self.risk_latest = repo.read_json("risk_latest.json", []) or []
        self.forecasts = repo.read_json("forecasts.json", []) or []
        self.alerts = repo.read_json(repo.ALERTS_JSON, []) or []
        self.sources = repo.read_json("sources.json", {}) or {}
        self.risk_ts = repo.read_frame(repo.RISK_PARQUET)
        self.signal_scores = repo.read_frame("signal_scores.parquet")
        self.signals = repo.read_signals()

    def geojson(self) -> dict:
        if self._geojson is None:
            path = get_settings().geojson_path
            with open(path, encoding="utf-8") as fh:
                self._geojson = json.load(fh)
        return self._geojson

    def districts(self) -> list[dict]:
        return [d.model_dump() for d in get_districts()]


state = AppState()
