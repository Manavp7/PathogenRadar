"""Phase 3.6 — fusion, outbreak classification, category inference, explainability."""

from __future__ import annotations

from datetime import date

import pandas as pd

from pathogenradar.acquisition.synthetic import SyntheticConnector, dengue_outbreak
from pathogenradar.detection.classifier import level_for
from pathogenradar.detection.engine import assess, latest_by_district
from pathogenradar.domain.models import DiseaseCategory, OutbreakLevel
from pathogenradar.features.pipeline import aggregate_sources
from pathogenradar.fusion.fuser import risk_score
from pathogenradar.quality.engine import assess as assess_quality
from pathogenradar.regions import get_districts
from pathogenradar.signals.service import run_detectors

START = date(2024, 1, 1)
END = date(2024, 6, 30)


def _pipeline_to_assessments():
    ob = dengue_outbreak("ernakulam", date(2024, 3, 1), magnitude=1.9)
    recs = SyntheticConnector(outbreaks=[ob]).fetch(get_districts(), START, END)
    raw = pd.DataFrame(
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
    quality = assess_quality(raw)
    agg = aggregate_sources(raw, quality.source_reliability)
    scores = run_detectors(agg)
    conf_by_day = {(r.district_id, r.date): r.confidence for r in quality.reports}
    return assess(scores, agg, conf_by_day)


def test_level_thresholds():
    assert level_for(5) == OutbreakLevel.NORMAL
    assert level_for(20) == OutbreakLevel.WATCH
    assert level_for(40) == OutbreakLevel.WARNING
    assert level_for(60) == OutbreakLevel.ALERT
    assert level_for(80) == OutbreakLevel.EMERGENCY


def test_fusion_monotonic_in_scores():
    low = risk_score({"hospital": 0.1, "search": 0.1})
    high = risk_score({"hospital": 0.9, "search": 0.9})
    assert high > low
    assert 0 <= low <= 100 and 0 <= high <= 100


def test_outbreak_district_classified_and_explained():
    assessments = _pipeline_to_assessments()
    # Find Ernakulam's peak risk during the outbreak window.
    ek = [
        a
        for a in assessments
        if a.district_id == "ernakulam" and date(2024, 3, 15) <= a.date <= date(2024, 4, 15)
    ]
    peak = max(ek, key=lambda a: a.risk_score)

    assert peak.risk_score >= 35  # at least Warning
    assert peak.level in {OutbreakLevel.WARNING, OutbreakLevel.ALERT, OutbreakLevel.EMERGENCY}
    assert peak.category == DiseaseCategory.VECTOR
    assert any("Dengue" in d or "Chikungunya" in d for d in peak.likely_diseases)
    # Explainability present with concrete drivers.
    assert peak.contributions
    labels = {c.label for c in peak.contributions}
    assert any("searches" in label.lower() or "admissions" in label.lower() for label in labels)


def test_quiet_districts_stay_normal():
    assessments = _pipeline_to_assessments()
    latest = latest_by_district(assessments)
    # A far-away district with no outbreak should be calm at the start of the series.
    early = [a for a in assessments if a.district_id == "kasaragod" and a.date < date(2024, 2, 15)]
    assert all(a.level in {OutbreakLevel.NORMAL, OutbreakLevel.WATCH} for a in early)
    assert "ernakulam" in latest
