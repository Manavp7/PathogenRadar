"""P3.1 — multi-state scaling: a second region (Tamil Nadu) derived from config + GeoJSON."""

from __future__ import annotations

from datetime import date

import networkx as nx

from pathogenradar.detection.engine import latest_by_district
from pathogenradar.domain.models import DiseaseCategory
from pathogenradar.regions import available_regions, build_district_graph, get_districts
from pathogenradar.scenarios import run_scenario


def test_two_regions_available():
    regions = available_regions()
    assert "kerala" in regions
    assert "tamil_nadu" in regions


def test_tamil_nadu_derived_from_geojson():
    tn = get_districts("tamil_nadu")
    assert len(tn) >= 25  # ~30 districts
    # Auto-derived adjacency forms a connected graph with no isolated districts.
    g = build_district_graph("tamil_nadu")
    assert nx.is_connected(g)
    assert all(d.neighbors for d in tn)
    assert all(d.population > 0 for d in tn)


def test_pipeline_runs_for_second_region():
    result = run_scenario("dengue", as_of=date(2024, 6, 30), persist=False, region="tamil_nadu")
    assert result.region_key == "tamil_nadu"
    latest = latest_by_district(result.assessments)
    assert len(latest) == len(get_districts("tamil_nadu"))
    # The seeded (most populous) TN district should be elevated and vector-classified.
    peak = max(result.assessments, key=lambda a: a.risk_score)
    assert peak.risk_score >= 35
    assert peak.category == DiseaseCategory.VECTOR


def test_regions_are_independent():
    # Kerala still uses its explicit, accurate config (not derived).
    kerala = get_districts("kerala")
    assert len(kerala) == 14
    assert any(d.id == "ernakulam" for d in kerala)
