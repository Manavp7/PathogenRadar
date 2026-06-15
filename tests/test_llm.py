"""Phase 3.10 — LLM briefing provider abstraction (offline by default)."""

from __future__ import annotations

from datetime import date

from pathogenradar.llm import TemplateBriefingProvider, get_briefing_provider
from pathogenradar.llm.briefing import generate_briefing

RISK_LATEST = [
    {
        "district_id": "ernakulam",
        "district_name": "Ernakulam",
        "risk_score": 82.0,
        "level": "Emergency",
        "category": "Vector",
        "likely_diseases": ["Dengue", "Chikungunya"],
    },
    {
        "district_id": "kasaragod",
        "district_name": "Kasaragod",
        "risk_score": 5.0,
        "level": "Normal",
        "category": "Unknown",
        "likely_diseases": [],
    },
]
FORECASTS = [
    {
        "district_id": "thrissur",
        "district_name": "Thrissur",
        "points": [{"horizon_days": 30, "risk_probability": 0.81}],
    },
    {
        "district_id": "ernakulam",
        "district_name": "Ernakulam",
        "points": [{"horizon_days": 30, "risk_probability": 0.99}],
    },
]


def test_default_provider_is_template_offline():
    provider = get_briefing_provider()
    assert provider.name == "template"
    assert isinstance(provider, TemplateBriefingProvider)


def test_briefing_generated_without_any_api_key():
    briefing = generate_briefing(
        region="Kerala",
        as_of=date(2024, 3, 20),
        risk_latest=RISK_LATEST,
        forecasts=FORECASTS,
        source_summary={"synthetic": "ok"},
    )
    assert briefing.provider == "template"
    assert "Kerala" in briefing.body
    assert "Ernakulam" in briefing.body
    # Forecast highlight should surface a neighbouring district, not the hotspot itself.
    assert "Thrissur" in briefing.body
    assert "Recommended Actions" in briefing.body


def test_briefing_handles_all_normal():
    calm = [{**RISK_LATEST[1]}]
    briefing = generate_briefing("Kerala", date(2024, 1, 1), calm, [])
    assert "No districts" in briefing.body or "routine" in briefing.body.lower()
