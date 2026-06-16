"""Wastewater viral-load anomaly detector (robust change-point via rolling z-score)."""

from __future__ import annotations

from ..domain.models import SignalScore, SignalType
from .base import Detector
from .common import anomaly_from_z, rolling_robust_z

WASTEWATER_TYPE = SignalType.WASTEWATER_VIRAL_LOAD.value


class WastewaterDetector(Detector):
    name = "wastewater"

    def detect(self, df_agg):
        scores: list[SignalScore] = []
        sub = df_agg[df_agg["signal_type"] == WASTEWATER_TYPE]
        for district_id, grp in sub.groupby("district_id", sort=False):
            series = grp.sort_values("date").set_index("date")["value"]
            z = rolling_robust_z(series)
            for day, zval in z.items():
                anom = anomaly_from_z(float(zval))
                scores.append(
                    SignalScore(
                        district_id=district_id,
                        date=day.date() if hasattr(day, "date") else day,
                        detector=self.name,
                        score=round(anom, 4),
                        drivers={"wastewater_viral_load": round(anom, 3)} if anom > 0.01 else {},
                    )
                )
        return scores
