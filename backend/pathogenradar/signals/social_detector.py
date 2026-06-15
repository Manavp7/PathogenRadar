"""Social-signal anomaly detector.

Operates on aggregated social mention volume. (Phase 2 will add transformer-based NLP for
symptom/location/severity extraction from raw text; here we score mention-volume anomalies.)
"""

from __future__ import annotations

from ..domain.models import SignalScore, SignalType
from .base import Detector
from .common import anomaly_from_z, rolling_robust_z

SOCIAL_TYPE = SignalType.SOCIAL_MENTIONS.value


class SocialDetector(Detector):
    name = "social"

    def detect(self, df_agg):
        scores: list[SignalScore] = []
        sub = df_agg[df_agg["signal_type"] == SOCIAL_TYPE]
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
                        drivers={"social_mentions": round(anom, 3)} if anom > 0.01 else {},
                    )
                )
        return scores
