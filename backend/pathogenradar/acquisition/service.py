"""Acquisition orchestration.

Runs the synthetic source (always) plus any enabled real connectors (Google Trends,
OpenWeather), combining them into a single multi-source signal stream. Real connectors are
optional and degrade gracefully — the platform is fully functional offline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from ..config import get_settings
from ..domain.models import SignalRecord
from ..regions import get_districts
from .base import Connector, FetchResult
from .google_trends import GoogleTrendsConnector
from .synthetic import OutbreakEvent, SyntheticConnector
from .weather import OpenWeatherConnector

logger = logging.getLogger("pathogenradar.acquisition.service")


@dataclass
class AcquisitionResult:
    records: list[SignalRecord]
    sources: list[FetchResult]

    @property
    def source_summary(self) -> dict[str, str]:
        return {r.source_id: r.status for r in self.sources}


def build_connectors(outbreaks: list[OutbreakEvent] | None = None) -> list[Connector]:
    settings = get_settings()
    connectors: list[Connector] = [SyntheticConnector(outbreaks=outbreaks)]

    if settings.enable_google_trends:
        logger.info("Google Trends connector ENABLED (geo=IN-KL)")
        connectors.append(GoogleTrendsConnector())

    if settings.openweather_api_key:
        logger.info("OpenWeather connector ENABLED")
        connectors.append(OpenWeatherConnector(settings.openweather_api_key))

    if settings.fhir_base_url:
        from .fhir import FHIRConnector

        logger.info("ABDM/FHIR connector ENABLED (%s)", settings.fhir_base_url)
        connectors.append(FHIRConnector(base_url=settings.fhir_base_url))

    return connectors


def acquire(
    start: date,
    end: date,
    outbreaks: list[OutbreakEvent] | None = None,
    region: str | None = None,
) -> AcquisitionResult:
    """Acquire signals from all active connectors for the date range."""
    districts = get_districts(region)
    results: list[FetchResult] = []
    records: list[SignalRecord] = []

    for connector in build_connectors(outbreaks):
        res = connector.safe_fetch(districts, start, end)
        results.append(res)
        records.extend(res.records)
        logger.info(
            "source=%s status=%s records=%d live=%s",
            res.source_id,
            res.status,
            len(res.records),
            res.live,
        )

    return AcquisitionResult(records=records, sources=results)
