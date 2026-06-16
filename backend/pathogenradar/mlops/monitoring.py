"""Drift monitoring + retraining trigger.

Computes Population Stability Index (PSI) between a baseline window and the recent window of
each signal (region-wide daily mean) and recommends retraining when distribution drift is high.
"""

from __future__ import annotations

import pandas as pd

from ..quality.detectors import psi
from ..store import repo

MODERATE_PSI = 0.1
HIGH_PSI = 0.25


def _drift_level(value: float) -> str:
    if value >= HIGH_PSI:
        return "high"
    if value >= MODERATE_PSI:
        return "moderate"
    return "stable"


def drift_report(region: str | None = None, recent_frac: float = 0.2) -> dict:
    df = repo.read_signals(region)
    if df.empty:
        return {"signals": [], "max_psi": 0.0, "retrain_recommended": False}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    signals = []
    for signal_type, grp in df.groupby("signal_type"):
        daily = grp.groupby("date")["value"].mean().sort_index().reset_index(drop=True)
        if len(daily) < 30:
            continue
        cut = int(len(daily) * (1 - recent_frac))
        value = psi(daily.iloc[:cut], daily.iloc[cut:])
        signals.append(
            {"signal": signal_type, "psi": round(float(value), 4), "level": _drift_level(value)}
        )

    signals.sort(key=lambda s: s["psi"], reverse=True)
    max_psi = signals[0]["psi"] if signals else 0.0
    return {
        "signals": signals,
        "max_psi": max_psi,
        "drifting_signals": [s["signal"] for s in signals if s["level"] != "stable"],
        "retrain_recommended": max_psi >= HIGH_PSI,
    }
