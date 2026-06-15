"""Phase 3.3 — synthetic generation, injectable outbreaks, offline orchestration."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from pathogenradar.acquisition.service import acquire
from pathogenradar.acquisition.synthetic import SyntheticConnector, dengue_outbreak
from pathogenradar.domain.models import SignalType
from pathogenradar.regions import get_districts

START = date(2024, 1, 1)
END = date(2024, 6, 30)


def _frame(records):
    return pd.DataFrame(
        [
            {
                "district_id": r.district_id,
                "date": pd.Timestamp(r.date),
                "signal_type": r.signal_type.value,
                "value": r.value,
            }
            for r in records
        ]
    )


def test_synthetic_covers_all_districts_and_signals():
    conn = SyntheticConnector()
    recs = conn.fetch(get_districts(), START, START + timedelta(days=6))
    df = _frame(recs)
    assert df["district_id"].nunique() == 14
    # 7 days * 14 districts * N signal types
    n_signals = df["signal_type"].nunique()
    assert len(df) == 7 * 14 * n_signals


def test_search_index_is_bounded():
    conn = SyntheticConnector()
    recs = conn.fetch(get_districts(), START, END)
    df = _frame(recs)
    search = df[df["signal_type"] == SignalType.SEARCH_FEVER.value]
    assert search["value"].min() >= 0.0
    assert search["value"].max() <= 100.0


def test_dengue_outbreak_raises_relevant_signals():
    outbreak = dengue_outbreak("ernakulam", date(2024, 3, 1), magnitude=1.8)
    conn = SyntheticConnector(outbreaks=[outbreak])
    df = _frame(conn.fetch(get_districts(), START, END))

    window = (df["date"] >= "2024-03-15") & (df["date"] <= "2024-04-05")
    fever = df[(df["signal_type"] == SignalType.SEARCH_FEVER.value) & window]

    ek = fever[fever["district_id"] == "ernakulam"]["value"].mean()
    ks = fever[fever["district_id"] == "kasaragod"]["value"].mean()
    # Outbreak district fever searches should clearly exceed an unaffected district.
    assert ek > ks * 1.4

    # A non-dengue signal (cough) should NOT be meaningfully elevated.
    cough = df[(df["signal_type"] == SignalType.SEARCH_COUGH.value) & window]
    ek_c = cough[cough["district_id"] == "ernakulam"]["value"].mean()
    ks_c = cough[cough["district_id"] == "kasaragod"]["value"].mean()
    assert ek_c < ks_c * 1.25


def test_acquire_offline_uses_only_synthetic():
    result = acquire(START, START + timedelta(days=3))
    assert result.source_summary == {"synthetic": "ok"}
    assert len(result.records) > 0
    assert all(r.source_id == "synthetic" for r in result.records)
