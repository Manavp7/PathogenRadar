"""Phase 3.5 — signal detectors flag a seeded outbreak in the right place/time."""

from __future__ import annotations

from datetime import date

import pandas as pd

from pathogenradar.acquisition.synthetic import SyntheticConnector, dengue_outbreak
from pathogenradar.features.pipeline import aggregate_sources
from pathogenradar.regions import get_districts
from pathogenradar.signals.service import run_detectors, scores_to_frame

START = date(2024, 1, 1)
END = date(2024, 6, 30)
OUTBREAK_START = date(2024, 3, 1)


def _agg_with_outbreak():
    ob = dengue_outbreak("ernakulam", OUTBREAK_START, magnitude=1.8)
    recs = SyntheticConnector(outbreaks=[ob]).fetch(get_districts(), START, END)
    df = pd.DataFrame(
        [
            {
                "district_id": r.district_id,
                "date": pd.Timestamp(r.date),
                "signal_type": r.signal_type.value,
                "value": r.value,
                "source_id": r.source_id,
            }
            for r in recs
        ]
    )
    return aggregate_sources(df)


def test_detectors_flag_outbreak_district_and_window():
    agg = _agg_with_outbreak()
    scores = run_detectors(agg)
    wide = scores_to_frame(scores)

    window = (wide["date"] >= "2024-03-15") & (wide["date"] <= "2024-04-10")
    ek = wide[(wide["district_id"] == "ernakulam") & window]
    ks = wide[(wide["district_id"] == "kasaragod") & window]

    # Search + hospital detectors fire strongly; wastewater is a weaker dengue signal.
    assert ek["search"].max() > 0.5
    assert ek["hospital"].max() > 0.4
    assert ek["wastewater"].max() > 0.2

    # Outbreak district anomaly clearly exceeds an unaffected district.
    assert ek["search"].mean() > ks["search"].mean() + 0.15


def test_quiet_period_has_low_scores():
    agg = _agg_with_outbreak()
    scores = run_detectors(agg)
    wide = scores_to_frame(scores)
    # Before the outbreak, Ernakulam should look calm.
    pre = wide[(wide["district_id"] == "ernakulam") & (wide["date"] < "2024-02-15")]
    assert pre["search"].mean() < 0.2
    assert pre["hospital"].mean() < 0.2
