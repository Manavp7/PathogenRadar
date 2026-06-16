"""Detector interface for the signal-intelligence layer.

Each detector consumes the aggregated signal frame and emits a per-district/day anomaly
score in [0, 1] plus the driver signals that explain it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from ..domain.models import SignalRecord, SignalScore  # noqa: F401 (SignalRecord re-export)


class Detector(ABC):
    name: str = "base"

    @abstractmethod
    def detect(self, df_agg: pd.DataFrame) -> list[SignalScore]:
        """Return anomaly scores for an aggregated long frame.

        ``df_agg`` columns: district_id, date, signal_type, value.
        """
