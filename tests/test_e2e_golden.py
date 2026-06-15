"""Phase 3.12 — the golden end-to-end contract.

Encodes the Done Criteria: a synthetic dengue outbreak in one Kerala district must flow all
the way through detection → fusion → forecast → simulation → alert → briefing, exactly as the
dashboard presents it. This is the single test that proves "raw signals → executive decision".
"""

from __future__ import annotations

from datetime import date

from pathogenradar.detection.engine import latest_by_district
from pathogenradar.domain.models import DiseaseCategory, Intervention, OutbreakLevel
from pathogenradar.llm.briefing import generate_briefing
from pathogenradar.pipeline import golden_scenario
from pathogenradar.simulation.seir import simulate

AS_OF = date(2024, 6, 30)


def test_golden_pipeline_end_to_end():
    result = golden_scenario(as_of=AS_OF, persist=False)
    latest = latest_by_district(result.assessments)

    # 1 & 2 & 3: outbreak detected and fused into a high risk score in the seeded district.
    ek = latest["ernakulam"]
    assert ek.risk_score >= 55  # Alert or Emergency
    assert ek.level in {OutbreakLevel.ALERT, OutbreakLevel.EMERGENCY}

    # Anomalies came from multiple independent signal families.
    assert ek.signal_scores.get("search", 0) > 0.5
    assert ek.signal_scores.get("hospital", 0) > 0.3

    # Correct disease category + plausible diseases (vector-borne).
    assert ek.category == DiseaseCategory.VECTOR
    assert any("Dengue" in d or "Chikungunya" in d for d in ek.likely_diseases)

    # Explainability present (the "why").
    assert ek.contributions
    assert any(
        "search" in c.label.lower() or "admission" in c.label.lower() for c in ek.contributions
    )

    # 4: every district has a risk value (the heatmap data).
    assert len(latest) == 14

    # 5: spread forecast predicts neighbouring districts ahead of far ones.
    fc = {f.district_id: f for f in result.forecasts}
    neighbour = fc["kottayam"].points[-1].risk_probability
    far = fc["kasaragod"].points[-1].risk_probability
    assert neighbour > far

    # 6: SEIR projects future cases and quantifies intervention impact.
    sim = simulate(
        "ernakulam", "dengue", intervention=Intervention(masking=0.8, vaccination_rate=0.3)
    )
    assert sim.peak_infected_baseline > 0
    assert sim.cases_averted and sim.cases_averted > 0

    # 7: an alert was generated for the outbreak district, escalated appropriately.
    ek_alerts = [a for a in result.alerts if a.district_id == "ernakulam"]
    assert ek_alerts
    assert ek_alerts[0].recommended_actions
    assert "dashboard" in ek_alerts[0].channels

    # 8: a minister briefing is generated offline (no LLM key required).
    briefing = generate_briefing(
        region=result.region,
        as_of=result.as_of,
        risk_latest=[a.model_dump(mode="json") for a in latest.values()],
        forecasts=[f.model_dump(mode="json") for f in result.forecasts],
        source_summary=result.source_summary,
    )
    assert briefing.provider == "template"
    assert "Kerala" in briefing.body
    assert "Ernakulam" in briefing.body

    # 9: the full chain is coherent — the source summary records the data provenance.
    assert "synthetic" in result.source_summary
