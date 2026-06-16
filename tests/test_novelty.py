"""P2.2 — novel-pathogen detection."""

from __future__ import annotations

from datetime import date

import pandas as pd

from pathogenradar.acquisition.synthetic import (
    SyntheticConnector,
    dengue_outbreak,
    novel_outbreak,
)
from pathogenradar.detection.engine import assess
from pathogenradar.detection.novelty import get_novelty_detector
from pathogenradar.features.pipeline import aggregate_sources
from pathogenradar.quality.engine import assess as assess_quality
from pathogenradar.regions import get_districts
from pathogenradar.signals.service import run_detectors

START = date(2024, 1, 1)
END = date(2024, 6, 30)


def _assess_with(outbreak):
    recs = SyntheticConnector(outbreaks=[outbreak]).fetch(get_districts(), START, END)
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
    q = assess_quality(raw)
    agg = aggregate_sources(raw, q.source_reliability)
    scores = run_detectors(agg)
    conf = {(r.district_id, r.date): r.confidence for r in q.reports}
    assessments = assess(scores, agg, conf)
    # Peak assessment per district (the outbreak peaks mid-series, not at the end).
    peak: dict = {}
    for a in assessments:
        cur = peak.get(a.district_id)
        if cur is None or a.risk_score > cur.risk_score:
            peak[a.district_id] = a
    return peak


def test_detector_discriminates_known_from_novel():
    nd = get_novelty_detector()
    dengue = {
        "search_fever": 0.9,
        "search_rash": 0.9,
        "hospital_admissions": 0.8,
        "lab_pcr_requests": 0.9,
    }
    novel = {
        "search_cough": 1.0,
        "search_diarrhea": 1.0,
        "search_rash": 1.0,
        "ventilator_usage": 0.9,
        "mortality": 0.9,
    }
    assert nd.score(dengue) < 0.4
    assert nd.score(novel) > 0.7


def test_known_dengue_is_not_flagged_novel():
    latest = _assess_with(dengue_outbreak("ernakulam", date(2024, 3, 1), magnitude=2.2))
    ek = latest["ernakulam"]
    assert ek.risk_score >= 55
    assert ek.novel_pathogen is False
    assert ek.novelty_score < 0.6


def test_novel_pathogen_is_flagged():
    latest = _assess_with(novel_outbreak("kozhikode", date(2024, 3, 1), magnitude=2.4))
    kkd = latest["kozhikode"]
    assert kkd.risk_score >= 55
    assert kkd.novel_pathogen is True
    assert kkd.novelty_score >= 0.6
    assert kkd.category.value == "Unknown"
