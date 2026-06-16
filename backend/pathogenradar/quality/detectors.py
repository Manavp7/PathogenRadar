"""Low-level data-quality detectors: missingness, robust outliers, and distribution drift.

These are deliberately *robust* (median/MAD based) so a genuine epidemiological outbreak is
NOT mistaken for a data error — only physically implausible glitches are flagged here. The
job of finding outbreak anomalies belongs to the signal-intelligence layer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Plausible ranges per signal family used for integrity checks.
SEARCH_MAX = 100.0
HUMIDITY_MAX = 100.0


def completeness(values: pd.Series, expected: int) -> float:
    """Fraction of expected observations that are present and non-null."""
    if expected <= 0:
        return 0.0
    present = int(values.notna().sum())
    return min(1.0, present / expected)


def robust_z(values: pd.Series) -> pd.Series:
    """Median/MAD z-scores (resistant to a few extreme points)."""
    v = values.astype(float)
    med = v.median()
    mad = (v - med).abs().median()
    if mad == 0 or np.isnan(mad):
        std = v.std(ddof=0)
        if std == 0 or np.isnan(std):
            return pd.Series(np.zeros(len(v)), index=v.index)
        return (v - med) / std
    return 0.6745 * (v - med) / mad


def outlier_ratio(values: pd.Series, threshold: float = 6.0) -> float:
    """Fraction of points that are extreme enough to look like data glitches."""
    if len(values) == 0:
        return 0.0
    z = robust_z(values).abs()
    return float((z > threshold).mean())


def integrity(values: pd.Series, signal_type: str) -> float:
    """1.0 = all values plausible; lower when negatives/out-of-range values appear."""
    if len(values) == 0:
        return 0.0
    v = values.astype(float)
    invalid = v.isna()
    # Counts and indices cannot be negative.
    invalid = invalid | (v < 0)
    if signal_type.startswith("search_"):
        invalid = invalid | (v > SEARCH_MAX)
    if signal_type == "weather_humidity":
        invalid = invalid | (v > HUMIDITY_MAX)
    return float(1.0 - invalid.mean())


def stability(values: pd.Series, window: int = 7) -> float:
    """1/(1+CV of de-trended residual). High random noise -> low stability.

    De-trending with a rolling median means a smooth outbreak ramp does NOT reduce
    stability — only erratic, noisy sources do.
    """
    v = values.astype(float).dropna()
    if len(v) < window + 1:
        return 1.0
    trend = v.rolling(window, center=True, min_periods=1).median()
    residual = v - trend
    level = max(abs(v.mean()), 1e-6)
    cv = residual.std(ddof=0) / level
    return float(1.0 / (1.0 + cv))


def psi(baseline: pd.Series, recent: pd.Series, bins: int = 10) -> float:
    """Population Stability Index between a baseline and a recent window (drift score)."""
    b = baseline.astype(float).dropna()
    r = recent.astype(float).dropna()
    if len(b) < bins or len(r) < bins:
        return 0.0
    edges = np.quantile(b, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    b_hist = np.histogram(b, bins=edges)[0] / len(b)
    r_hist = np.histogram(r, bins=edges)[0] / len(r)
    eps = 1e-6
    b_hist = np.clip(b_hist, eps, None)
    r_hist = np.clip(r_hist, eps, None)
    return float(np.sum((r_hist - b_hist) * np.log(r_hist / b_hist)))
