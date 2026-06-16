"""Feature engineering.

Collapses the multi-source signal stream into a single reliability-weighted value per
(district, date, signal) and exposes helpers for rolling statistics used by detectors.
"""

from __future__ import annotations

import pandas as pd

from ..domain.models import SourceReliability


def aggregate_sources(
    df: pd.DataFrame,
    source_reliability: dict[str, SourceReliability] | None = None,
) -> pd.DataFrame:
    """Combine multiple sources of the same signal via reliability-weighted averaging.

    Returns a long frame with columns: district_id, date, signal_type, value.
    """
    if df.empty:
        return df.assign(value=[]).loc[:, ["district_id", "date", "signal_type", "value"]]

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if source_reliability:
        weights = {s: max(r.reliability, 1e-3) for s, r in source_reliability.items()}
    else:
        weights = {}

    df["w"] = df["source_id"].map(lambda s: weights.get(s, 1.0))
    df["wv"] = df["w"] * df["value"]
    grouped = (
        df.groupby(["district_id", "date", "signal_type"], sort=False)
        .agg(wv=("wv", "sum"), w=("w", "sum"))
        .reset_index()
    )
    grouped["value"] = grouped["wv"] / grouped["w"]
    return grouped[["district_id", "date", "signal_type", "value"]]


def pivot_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Wide frame indexed by (district_id, date) with one column per signal_type."""
    wide = df.pivot_table(
        index=["district_id", "date"], columns="signal_type", values="value"
    ).reset_index()
    wide.columns.name = None
    return wide.sort_values(["district_id", "date"]).reset_index(drop=True)


def district_series(df: pd.DataFrame, district_id: str, signal_type: str) -> pd.Series:
    """Time-indexed value series for one district + signal."""
    sub = df[(df["district_id"] == district_id) & (df["signal_type"] == signal_type)]
    return sub.sort_values("date").set_index("date")["value"]
