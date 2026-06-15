"""Connector interface for data acquisition.

Every data source (synthetic, Google Trends, OpenWeather, future hospital/ABDM feeds)
implements ``Connector``. ``safe_fetch`` guarantees the platform never crashes on a flaky
external source — it returns whatever it can plus a status string, never raising.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..domain.models import District, SignalRecord, SignalType

logger = logging.getLogger("pathogenradar.acquisition")


@dataclass
class FetchResult:
    source_id: str
    records: list[SignalRecord]
    status: str  # "ok" | "fallback:<reason>" | "error:<reason>"
    live: bool  # True if data came from a real external service


class Connector(ABC):
    """Base class for all data connectors."""

    source_id: str = "base"
    provides: list[SignalType] = []

    @abstractmethod
    def fetch(self, districts: list[District], start: date, end: date) -> list[SignalRecord]:
        """Fetch raw signal records for the given districts and date range.

        May raise; callers should prefer :meth:`safe_fetch`.
        """

    @property
    def live(self) -> bool:
        """Whether this connector talks to a real external service in its current config."""
        return False

    def safe_fetch(self, districts: list[District], start: date, end: date) -> FetchResult:
        try:
            records = self.fetch(districts, start, end)
            return FetchResult(self.source_id, records, "ok", self.live)
        except Exception as exc:  # noqa: BLE001 - intentional: never crash the pipeline
            logger.warning("connector %s failed: %s", self.source_id, exc)
            return FetchResult(self.source_id, [], f"error:{exc}", False)
