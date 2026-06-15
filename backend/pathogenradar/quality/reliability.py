"""Source reliability scoring.

Each data source earns a trust score from its completeness, integrity and stability —
NOT from whether an outbreak is present. The model learns which sources to trust
(e.g. "Hospital A = 94%, Hospital B = 61%").
"""

from __future__ import annotations

import pandas as pd

from ..domain.models import SourceReliability
from . import detectors

# Weights for the composite reliability score.
W_COMPLETENESS = 0.5
W_INTEGRITY = 0.2
W_STABILITY = 0.3


def score_source(df_source: pd.DataFrame, expected_per_signal: int) -> SourceReliability:
    """Compute a reliability score for one source from its long-format records."""
    source_id = df_source["source_id"].iloc[0] if len(df_source) else "unknown"

    completeness_vals: list[float] = []
    integrity_vals: list[float] = []
    stability_vals: list[float] = []

    for (_, _signal), grp in df_source.groupby(["district_id", "signal_type"], sort=False):
        signal = grp["signal_type"].iloc[0]
        series = grp.sort_values("date")["value"]
        completeness_vals.append(detectors.completeness(series, expected_per_signal))
        integrity_vals.append(detectors.integrity(series, signal))
        stability_vals.append(detectors.stability(series))

    comp = _mean(completeness_vals)
    integ = _mean(integrity_vals)
    stab = _mean(stability_vals)
    reliability = W_COMPLETENESS * comp + W_INTEGRITY * integ + W_STABILITY * stab

    notes = []
    if comp < 0.9:
        notes.append(f"completeness {comp:.0%}")
    if integ < 0.99:
        notes.append(f"integrity issues {1 - integ:.0%}")
    if stab < 0.7:
        notes.append("noisy/unstable series")

    return SourceReliability(
        source_id=source_id,
        reliability=round(reliability, 4),
        completeness=round(comp, 4),
        stability=round(stab, 4),
        notes=notes,
    )


def _mean(xs: list[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else 0.0
