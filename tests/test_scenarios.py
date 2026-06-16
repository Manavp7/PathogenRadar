"""H5 — multi-scenario seeding: simultaneous outbreaks across disease categories."""

from __future__ import annotations

from datetime import date

from pathogenradar.detection.engine import latest_by_district
from pathogenradar.domain.models import DiseaseCategory, OutbreakLevel
from pathogenradar.scenarios import run_scenario

AS_OF = date(2024, 6, 30)
ELEVATED = {
    OutbreakLevel.WATCH,
    OutbreakLevel.WARNING,
    OutbreakLevel.ALERT,
    OutbreakLevel.EMERGENCY,
}


def test_multi_scenario_spans_three_categories():
    result = run_scenario("multi", as_of=AS_OF, persist=False)
    latest = latest_by_district(result.assessments)

    ek = latest["ernakulam"]  # dengue → vector
    tvm = latest["thiruvananthapuram"]  # ILI → respiratory
    kkd = latest["kozhikode"]  # cholera → waterborne

    assert ek.level in ELEVATED and ek.category == DiseaseCategory.VECTOR
    assert tvm.level in ELEVATED and tvm.category == DiseaseCategory.RESPIRATORY
    assert kkd.level in ELEVATED and kkd.category == DiseaseCategory.WATERBORNE

    # Three independent alerts spanning three categories.
    cats = {a.category for a in result.alerts}
    assert {DiseaseCategory.VECTOR, DiseaseCategory.RESPIRATORY, DiseaseCategory.WATERBORNE} <= cats


def test_single_scenarios_classify_correctly():
    resp = latest_by_district(run_scenario("respiratory", as_of=AS_OF, persist=False).assessments)
    assert resp["thiruvananthapuram"].category == DiseaseCategory.RESPIRATORY

    water = latest_by_district(run_scenario("waterborne", as_of=AS_OF, persist=False).assessments)
    assert water["kozhikode"].category == DiseaseCategory.WATERBORNE
