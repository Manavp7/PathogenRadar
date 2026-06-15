"""Data-quality engine.

Combines source reliability with per-district/day missingness, glitch-outliers and drift
into a single ``confidence`` score in [0, 1] used to quality-weight downstream fusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from ..domain.models import QualityReport, SourceReliability
from . import detectors
from .reliability import score_source


@dataclass
class QualityResult:
    reports: list[QualityReport]
    source_reliability: dict[str, SourceReliability]

    def confidence_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "district_id": r.district_id,
                    "date": pd.Timestamp(r.date),
                    "confidence": r.confidence,
                }
                for r in self.reports
            ]
        )


def assess(df: pd.DataFrame) -> QualityResult:
    """Assess data quality for a long-format signal DataFrame."""
    if df.empty:
        return QualityResult(reports=[], source_reliability={})

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    n_dates = df["date"].nunique()

    # --- Source reliability ---
    source_reliability: dict[str, SourceReliability] = {}
    for source_id, grp in df.groupby("source_id", sort=False):
        source_reliability[source_id] = score_source(grp, expected_per_signal=n_dates)

    # --- Drift score per (district, signal): PSI of recent window vs baseline ---
    drift_by_district = _drift_by_district(df)

    # --- Per district/day report ---
    expected_signals = df["signal_type"].nunique()
    mean_source_rel = (
        sum(s.reliability for s in source_reliability.values()) / len(source_reliability)
        if source_reliability
        else 0.0
    )

    reports: list[QualityReport] = []
    for (district_id, day), grp in df.groupby(["district_id", "date"], sort=False):
        present = grp["signal_type"].nunique()
        missing_ratio = max(0.0, 1.0 - present / expected_signals)
        out_ratio = detectors.outlier_ratio(grp["value"])
        drift = drift_by_district.get(district_id, 0.0)

        confidence = mean_source_rel * (1.0 - 0.6 * missing_ratio) * (1.0 - 0.3 * out_ratio)
        confidence = max(0.0, min(1.0, confidence))

        reports.append(
            QualityReport(
                district_id=district_id,
                date=day.date() if hasattr(day, "date") else day,
                confidence=round(confidence, 4),
                missing_ratio=round(missing_ratio, 4),
                outlier_ratio=round(out_ratio, 4),
                drift_score=round(float(drift), 4),
                sources=list(source_reliability.values()),
            )
        )

    return QualityResult(reports=reports, source_reliability=source_reliability)


def _drift_by_district(df: pd.DataFrame, recent_frac: float = 0.25) -> dict[str, float]:
    drift: dict[str, float] = {}
    for district_id, grp in df.groupby("district_id", sort=False):
        scores = []
        for _signal, sgrp in grp.groupby("signal_type", sort=False):
            s = sgrp.sort_values("date")["value"].reset_index(drop=True)
            if len(s) < 20:
                continue
            cut = int(len(s) * (1 - recent_frac))
            scores.append(detectors.psi(s.iloc[:cut], s.iloc[cut:]))
        drift[district_id] = sum(scores) / len(scores) if scores else 0.0
    return drift


def latest_confidence_map(result: QualityResult) -> dict[str, float]:
    """Confidence for each district on its most recent date."""
    by_district: dict[str, tuple[date, float]] = {}
    for r in result.reports:
        cur = by_district.get(r.district_id)
        if cur is None or r.date > cur[0]:
            by_district[r.district_id] = (r.date, r.confidence)
    return {k: v[1] for k, v in by_district.items()}
