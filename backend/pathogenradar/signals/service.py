"""Signal-intelligence orchestration: run every detector and collect anomaly scores."""

from __future__ import annotations

import pandas as pd

from ..domain.models import SignalScore
from .base import Detector
from .hospital_detector import HospitalDetector
from .search_detector import SearchDetector
from .social_detector import SocialDetector
from .wastewater_detector import WastewaterDetector


def default_detectors() -> list[Detector]:
    return [SearchDetector(), HospitalDetector(), SocialDetector(), WastewaterDetector()]


def run_detectors(
    df_agg: pd.DataFrame, detectors: list[Detector] | None = None
) -> list[SignalScore]:
    detectors = detectors or default_detectors()
    out: list[SignalScore] = []
    for det in detectors:
        out.extend(det.detect(df_agg))
    return out


def scores_to_frame(scores: list[SignalScore]) -> pd.DataFrame:
    """Wide frame: (district_id, date) x detector -> score."""
    rows = [
        {
            "district_id": s.district_id,
            "date": pd.Timestamp(s.date),
            "detector": s.detector,
            "score": s.score,
        }
        for s in scores
    ]
    if not rows:
        return pd.DataFrame(columns=["district_id", "date"])
    df = pd.DataFrame(rows)
    wide = df.pivot_table(
        index=["district_id", "date"], columns="detector", values="score"
    ).reset_index()
    wide.columns.name = None
    return wide
