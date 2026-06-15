"""Phase 3.4 — data quality engine: reliability, confidence, drift."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from pathogenradar.acquisition.synthetic import SyntheticConnector, dengue_outbreak
from pathogenradar.quality.engine import assess, latest_confidence_map
from pathogenradar.regions import get_districts

START = date(2024, 1, 1)
END = date(2024, 4, 30)


def _frame(records):
    return pd.DataFrame(
        [
            {
                "district_id": r.district_id,
                "date": pd.Timestamp(r.date),
                "signal_type": r.signal_type.value,
                "value": r.value,
                "source_id": r.source_id,
            }
            for r in records
        ]
    )


def _clean_frame():
    recs = SyntheticConnector().fetch(get_districts()[:3], START, END)
    return _frame(recs)


def test_clean_source_is_highly_reliable():
    df = _clean_frame()
    result = assess(df)
    rel = result.source_reliability["synthetic"]
    assert rel.reliability > 0.85
    assert rel.completeness == 1.0


def test_corrupted_source_loses_reliability():
    df = _clean_frame()
    clean_rel = assess(df).source_reliability["synthetic"].reliability

    corrupt = df.copy()
    rng = np.random.default_rng(0)
    idx = rng.choice(corrupt.index, size=int(len(corrupt) * 0.3), replace=False)
    # Inject missingness and impossible negative values.
    corrupt.loc[idx[: len(idx) // 2], "value"] = np.nan
    corrupt.loc[idx[len(idx) // 2 :], "value"] = -999.0
    corrupt_rel = assess(corrupt).source_reliability["synthetic"].reliability

    assert corrupt_rel < clean_rel
    assert corrupt_rel < 0.8


def test_confidence_attached_per_district_day():
    df = _clean_frame()
    result = assess(df)
    assert len(result.reports) == 3 * ((END - START).days + 1)
    assert all(0.0 <= r.confidence <= 1.0 for r in result.reports)
    conf_map = latest_confidence_map(result)
    assert set(conf_map) == {"kasaragod", "kannur", "wayanad"}
    assert all(0.0 <= c <= 1.0 for c in conf_map.values())


def test_outbreak_does_not_tank_confidence():
    """A real outbreak is signal, not a data error: confidence must stay high."""
    ob = dengue_outbreak("ernakulam", date(2024, 3, 1), magnitude=2.0)
    recs = SyntheticConnector(outbreaks=[ob]).fetch(get_districts(), START, END)
    result = assess(_frame(recs))
    conf = latest_confidence_map(result)
    assert conf["ernakulam"] > 0.8
