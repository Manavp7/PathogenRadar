"""Optional Google Trends connector (real public data via pytrends).

State-level search interest for symptom terms (geo=IN-KL) is fetched and broadcast across
districts as a realistic regional backdrop; the synthetic source still carries the
district-local outbreak spike. Results are cached to ``data/cache`` so the platform/tests
never depend on a live network. Disabled by default — enable with ``ENABLE_GOOGLE_TRENDS=true``.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from ..config import CACHE_DIR, ensure_dirs
from ..domain.models import District, SignalRecord, SignalType
from .base import Connector

logger = logging.getLogger("pathogenradar.acquisition.trends")

# Symptom search term -> signal type.
KEYWORD_MAP = {
    "fever": SignalType.SEARCH_FEVER,
    "cough": SignalType.SEARCH_COUGH,
    "rash": SignalType.SEARCH_RASH,
    "vomiting": SignalType.SEARCH_VOMITING,
    "diarrhea": SignalType.SEARCH_DIARRHEA,
}


class GoogleTrendsConnector(Connector):
    source_id = "google_trends"
    provides = list(KEYWORD_MAP.values())

    def __init__(self, geo: str = "IN-KL", tz: int = 330):
        self.geo = geo
        self.tz = tz

    @property
    def live(self) -> bool:
        return True

    def _cache_path(self, start: date, end: date):
        ensure_dirs()
        return CACHE_DIR / f"google_trends_{self.geo}_{start}_{end}.json"

    def _load_cache(self, start: date, end: date) -> dict | None:
        path = self._cache_path(start, end)
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        return None

    def _save_cache(self, start: date, end: date, payload: dict) -> None:
        with open(self._cache_path(start, end), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def _pull(self, start: date, end: date) -> dict[str, dict[str, float]]:
        """Return {keyword: {iso_date: value}}. Uses cache, else pytrends."""
        cached = self._load_cache(start, end)
        if cached is not None:
            logger.info("google_trends: using cached data for %s..%s", start, end)
            return cached

        # Live pull (may rate-limit / be blocked). Imported lazily so the dependency is
        # only needed when the connector is actually enabled.
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=self.tz)
        timeframe = f"{start.isoformat()} {end.isoformat()}"
        out: dict[str, dict[str, float]] = {}
        for kw in KEYWORD_MAP:
            pytrends.build_payload([kw], timeframe=timeframe, geo=self.geo)
            df = pytrends.interest_over_time()
            if df is None or df.empty or kw not in df:
                out[kw] = {}
                continue
            out[kw] = {ts.date().isoformat(): float(v) for ts, v in df[kw].items()}
        self._save_cache(start, end, out)
        return out

    def fetch(self, districts: list[District], start: date, end: date) -> list[SignalRecord]:
        series = self._pull(start, end)
        if not any(series.values()):
            return []  # nothing usable -> synthetic source covers search signals

        ndays = (end - start).days + 1
        all_dates = [start + timedelta(days=i) for i in range(ndays)]
        records: list[SignalRecord] = []
        for kw, signal in KEYWORD_MAP.items():
            points = series.get(kw) or {}
            if not points:
                continue
            daily = _resample_daily(points, all_dates)
            for district in districts:
                for d in all_dates:
                    records.append(
                        SignalRecord(
                            district_id=district.id,
                            date=d,
                            signal_type=signal,
                            value=round(daily[d], 3),
                            source_id=self.source_id,
                        )
                    )
        return records


def _resample_daily(points: dict[str, float], all_dates: list[date]) -> dict[date, float]:
    """Forward-fill a sparse (possibly weekly) series onto a daily grid."""
    parsed = sorted((datetime.fromisoformat(k).date(), v) for k, v in points.items())
    result: dict[date, float] = {}
    last = parsed[0][1] if parsed else 0.0
    idx = 0
    for d in all_dates:
        while idx < len(parsed) and parsed[idx][0] <= d:
            last = parsed[idx][1]
            idx += 1
        result[d] = last
    return result
