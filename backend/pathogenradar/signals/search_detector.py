"""Search-trend anomaly detector (STL deseasonalisation + robust z-score)."""

from __future__ import annotations

import pandas as pd

from ..domain.models import SEARCH_SIGNALS, SignalScore
from .base import Detector
from .common import anomaly_from_z, stl_residual_z

SEARCH_TYPES = [s.value for s in SEARCH_SIGNALS]


class SearchDetector(Detector):
    name = "search"

    def detect(self, df_agg: pd.DataFrame) -> list[SignalScore]:
        scores: list[SignalScore] = []
        sub = df_agg[df_agg["signal_type"].isin(SEARCH_TYPES)]
        for district_id, grp in sub.groupby("district_id", sort=False):
            wide = grp.pivot_table(index="date", columns="signal_type", values="value").sort_index()
            anomalies = pd.DataFrame(index=wide.index)
            for col in wide.columns:
                z = stl_residual_z(wide[col])
                anomalies[col] = z.map(anomaly_from_z)

            for day, row in anomalies.iterrows():
                drivers = {c: round(float(row[c]), 3) for c in anomalies.columns if row[c] > 0.01}
                score = _corroborated(list(row.values))
                scores.append(
                    SignalScore(
                        district_id=district_id,
                        date=day.date() if hasattr(day, "date") else day,
                        detector=self.name,
                        score=round(score, 4),
                        drivers=drivers,
                    )
                )
        return scores


def _corroborated(values: list[float]) -> float:
    """Reward corroboration across symptom terms (top-2 weighted).

    A single noisy term cannot dominate; a real syndrome (e.g. fever + rash for dengue)
    elevates multiple terms together and scores highly.
    """
    vals = sorted((max(0.0, min(1.0, v)) for v in values), reverse=True)
    if not vals:
        return 0.0
    top1 = vals[0]
    top2 = vals[1] if len(vals) > 1 else 0.0
    return round(0.6 * top1 + 0.4 * top2, 4)
