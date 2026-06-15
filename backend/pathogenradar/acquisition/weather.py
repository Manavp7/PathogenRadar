"""Optional OpenWeather connector (real current conditions).

Enabled only when ``OPENWEATHER_API_KEY`` is set. The free tier exposes current conditions
(not deep history), so this connector anchors the most recent days to real observations per
district; the synthetic source provides the seasonal weather backdrop otherwise. Responses
are cached. By default (no key) this connector is not constructed and weather is synthetic.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

import requests

from ..config import CACHE_DIR, ensure_dirs
from ..domain.models import District, SignalRecord, SignalType
from .base import Connector

logger = logging.getLogger("pathogenradar.acquisition.weather")

API_URL = "https://api.openweathermap.org/data/2.5/weather"


class OpenWeatherConnector(Connector):
    source_id = "openweather"
    provides = [SignalType.WEATHER_TEMP, SignalType.WEATHER_HUMIDITY, SignalType.WEATHER_RAINFALL]

    def __init__(self, api_key: str, anchor_days: int = 3, timeout: float = 10.0):
        self.api_key = api_key
        self.anchor_days = anchor_days
        self.timeout = timeout

    @property
    def live(self) -> bool:
        return True

    def _cache_path(self, district_id: str, day: date):
        ensure_dirs()
        return CACHE_DIR / f"openweather_{district_id}_{day}.json"

    def _current(self, district: District, day: date) -> dict | None:
        path = self._cache_path(district.id, day)
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        resp = requests.get(
            API_URL,
            params={
                "lat": district.lat,
                "lon": district.lon,
                "appid": self.api_key,
                "units": "metric",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return data

    def fetch(self, districts: list[District], start: date, end: date) -> list[SignalRecord]:
        today = datetime.utcnow().date()
        # Only anchor the most recent days that fall within the requested window.
        anchor_dates = [
            d
            for d in (end - timedelta(days=i) for i in range(self.anchor_days))
            if start <= d <= end and d <= today
        ]
        if not anchor_dates:
            return []

        records: list[SignalRecord] = []
        for district in districts:
            data = self._current(district, today)
            if not data:
                continue
            temp = data.get("main", {}).get("temp")
            humidity = data.get("main", {}).get("humidity")
            rainfall = data.get("rain", {}).get("1h", 0.0) * 24.0  # crude mm/day estimate
            for d in anchor_dates:
                if temp is not None:
                    records.append(self._rec(district.id, d, SignalType.WEATHER_TEMP, temp))
                if humidity is not None:
                    records.append(self._rec(district.id, d, SignalType.WEATHER_HUMIDITY, humidity))
                records.append(self._rec(district.id, d, SignalType.WEATHER_RAINFALL, rainfall))
        return records

    def _rec(self, district_id: str, d: date, signal: SignalType, value: float) -> SignalRecord:
        return SignalRecord(
            district_id=district_id,
            date=d,
            signal_type=signal,
            value=round(float(value), 3),
            source_id=self.source_id,
        )
