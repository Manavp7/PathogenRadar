"""Shared helpers for the signal-intelligence (anomaly detection) layer."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_robust_z(series: pd.Series, window: int = 42, min_periods: int = 14) -> pd.Series:
    """Trailing median/MAD z-score: how anomalous is each point vs its recent past."""
    v = series.astype(float)
    med = v.rolling(window, min_periods=min_periods).median()
    mad = (v - med).abs().rolling(window, min_periods=min_periods).median()
    # Fall back to rolling std where MAD collapses to 0.
    std = v.rolling(window, min_periods=min_periods).std(ddof=0)
    scale = (mad / 0.6745).where(mad > 0, std)
    z = (v - med) / scale.replace(0, np.nan)
    return z.fillna(0.0)


def stl_residual_z(series: pd.Series, period: int = 7, window: int = 42) -> pd.Series:
    """Remove *weekly seasonality* with STL, then robust-z the deseasonalised series.

    We deliberately keep the trend component: a sustained outbreak ramp lives in the trend,
    and removing it (as a plain STL residual would) hides exactly what we want to detect.
    Falls back to plain rolling-z for short series or if STL is unavailable.
    """
    v = series.astype(float)
    if len(v) < 2 * period + 2:
        return rolling_robust_z(v, window=window)
    try:
        from statsmodels.tsa.seasonal import STL

        res = STL(v.values, period=period, robust=True).fit()
        deseasonalised = pd.Series(v.values - res.seasonal, index=v.index)
        return rolling_robust_z(deseasonalised, window=window)
    except Exception:  # noqa: BLE001 - STL is best-effort; rolling-z is a fine fallback
        return rolling_robust_z(v, window=window)


def anomaly_from_z(z: float, low: float = 2.0, high: float = 6.0) -> float:
    """Map a (signed) z-score to a 0..1 anomaly intensity. Only positive excursions count."""
    if z <= low:
        return 0.0
    return float(min(1.0, (z - low) / (high - low)))
