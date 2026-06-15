"""Hospital-signal anomaly detector.

Combines a directional robust-z elevation score (admissions/ICU/ventilator/mortality/PCR)
with a multivariate IsolationForest context score. The z-component guarantees we react to
genuine elevations; IsolationForest adds multivariate sensitivity to unusual joint patterns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ..domain.models import HOSPITAL_SIGNALS, SignalScore
from .base import Detector
from .common import anomaly_from_z, rolling_robust_z

HOSPITAL_TYPES = [s.value for s in HOSPITAL_SIGNALS]


class HospitalDetector(Detector):
    name = "hospital"

    def detect(self, df_agg: pd.DataFrame) -> list[SignalScore]:
        scores: list[SignalScore] = []
        sub = df_agg[df_agg["signal_type"].isin(HOSPITAL_TYPES)]
        for district_id, grp in sub.groupby("district_id", sort=False):
            wide = grp.pivot_table(index="date", columns="signal_type", values="value").sort_index()
            if wide.empty:
                continue

            # Per-signal directional anomaly (positive elevation only).
            z = pd.DataFrame({c: rolling_robust_z(wide[c]) for c in wide.columns}, index=wide.index)
            per_signal_anom = z.clip(lower=0).map(anomaly_from_z)
            base = per_signal_anom.mean(axis=1)

            iso01 = self._isolation_context(z)

            for day in wide.index:
                b = float(base.loc[day])
                ctx = float(iso01.loc[day])
                score = min(1.0, b * (1.0 + 0.4 * ctx))
                drivers = {
                    c: round(float(per_signal_anom.loc[day, c]), 3)
                    for c in per_signal_anom.columns
                    if per_signal_anom.loc[day, c] > 0.01
                }
                if ctx > 0.01:
                    drivers["multivariate_context"] = round(ctx, 3)
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

    @staticmethod
    def _isolation_context(z: pd.DataFrame) -> pd.Series:
        """0..1 multivariate anomaly score from IsolationForest over the z-feature matrix."""
        x = z.fillna(0.0).values
        if len(x) < 20:
            return pd.Series(np.zeros(len(z)), index=z.index)
        clf = IsolationForest(n_estimators=120, contamination="auto", random_state=42)
        clf.fit(x)
        raw = -clf.score_samples(x)  # higher = more anomalous
        lo, hi = np.percentile(raw, 50), np.percentile(raw, 99)
        if hi <= lo:
            return pd.Series(np.zeros(len(z)), index=z.index)
        norm = np.clip((raw - lo) / (hi - lo), 0.0, 1.0)
        return pd.Series(norm, index=z.index)
