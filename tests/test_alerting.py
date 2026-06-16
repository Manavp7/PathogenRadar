"""Phase 3.9 — alerting engine."""

from __future__ import annotations

from datetime import date

from pathogenradar.alerting.engine import generate_alerts
from pathogenradar.domain.models import (
    Contribution,
    DiseaseCategory,
    OutbreakLevel,
    RiskAssessment,
)


def _assessment(level: OutbreakLevel, risk: float, category=DiseaseCategory.VECTOR):
    return RiskAssessment(
        district_id="ernakulam",
        district_name="Ernakulam",
        date=date(2024, 3, 20),
        risk_score=risk,
        level=level,
        category=category,
        likely_diseases=["Dengue", "Chikungunya"],
        confidence=0.92,
        signal_scores={"search": 0.9, "hospital": 0.7},
        contributions=[
            Contribution(label="Fever searches", value=120.0, detail="+120% vs baseline")
        ],
    )


def test_normal_produces_no_alert():
    assert generate_alerts([_assessment(OutbreakLevel.NORMAL, 5)]) == []


def test_emergency_uses_all_channels_and_actions():
    alerts = generate_alerts([_assessment(OutbreakLevel.EMERGENCY, 82)])
    assert len(alerts) == 1
    a = alerts[0]
    assert set(a.channels) == {"dashboard", "email", "sms", "whatsapp"}
    assert a.recommended_actions
    assert any("vector" in act.lower() or "fogging" in act.lower() for act in a.recommended_actions)
    assert "Dengue" in " ".join(a.reasons)


def test_alerts_sorted_by_severity():
    alerts = generate_alerts(
        [
            _assessment(OutbreakLevel.WATCH, 20),
            _assessment(OutbreakLevel.EMERGENCY, 82),
            _assessment(OutbreakLevel.WARNING, 40),
        ]
    )
    levels = [a.level for a in alerts]
    assert levels[0] == OutbreakLevel.EMERGENCY


def test_min_level_filter():
    alerts = generate_alerts([_assessment(OutbreakLevel.WATCH, 20)], min_level=OutbreakLevel.ALERT)
    assert alerts == []
