"""Alerting engine: turn risk assessments into actionable, escalated alerts.

Rule-based (deterministic) escalation from Watch → Emergency, with channel routing and
category-specific recommended interventions. No LLM involved.
"""

from __future__ import annotations

import hashlib

from ..domain.models import Alert, DiseaseCategory, OutbreakLevel, RiskAssessment

# Notification channels by escalation level (cumulative).
CHANNELS_BY_LEVEL: dict[OutbreakLevel, list[str]] = {
    OutbreakLevel.WATCH: ["dashboard"],
    OutbreakLevel.WARNING: ["dashboard", "email"],
    OutbreakLevel.ALERT: ["dashboard", "email", "sms"],
    OutbreakLevel.EMERGENCY: ["dashboard", "email", "sms", "whatsapp"],
}

# Category-specific recommended interventions.
ACTIONS_BY_CATEGORY: dict[DiseaseCategory, list[str]] = {
    DiseaseCategory.VECTOR: [
        "Launch vector-control & fogging drives in affected wards",
        "Eliminate stagnant-water breeding sites; public awareness on dengue prevention",
        "Pre-position platelet stocks and dengue NS1/IgM test kits",
    ],
    DiseaseCategory.RESPIRATORY: [
        "Reinforce mask advisories and respiratory hygiene messaging",
        "Audit oxygen, ICU and ventilator capacity in district hospitals",
        "Expand respiratory-panel PCR testing at sentinel sites",
    ],
    DiseaseCategory.WATERBORNE: [
        "Issue boil-water advisory; inspect and chlorinate water supply",
        "Deploy ORS and IV-fluid stocks to PHCs",
        "Test drinking-water sources and sewage cross-contamination points",
    ],
    DiseaseCategory.FOODBORNE: [
        "Inspect food vendors and recent common-source events",
        "Stock ORS/antiemetics at PHCs; trace suspected food source",
    ],
    DiseaseCategory.UNKNOWN: [
        "Dispatch rapid-response team for field epidemiological investigation",
        "Collect samples for syndromic and metagenomic testing",
    ],
}

LEVEL_ACTIONS: dict[OutbreakLevel, str] = {
    OutbreakLevel.WATCH: "Continue monitoring; verify signal with district surveillance officer",
    OutbreakLevel.WARNING: "Activate district surveillance unit; daily situation reporting",
    OutbreakLevel.ALERT: "Convene district rapid-response team; brief health administration",
    OutbreakLevel.EMERGENCY: "Escalate to State Control Room; activate emergency response plan",
}


def generate_alerts(
    assessments: list[RiskAssessment],
    min_level: OutbreakLevel = OutbreakLevel.WATCH,
) -> list[Alert]:
    """Generate alerts for the given (typically latest-per-district) assessments."""
    order = list(CHANNELS_BY_LEVEL.keys())
    threshold = order.index(min_level)
    alerts: list[Alert] = []
    for a in assessments:
        if a.level == OutbreakLevel.NORMAL:
            continue
        if order.index(a.level) < threshold:
            continue
        alerts.append(_build_alert(a))
    # Most severe first, then by risk.
    severity = {lvl: i for i, lvl in enumerate(order)}
    alerts.sort(key=lambda al: (severity.get(al.level, 0), al.risk_score), reverse=True)
    return alerts


def _build_alert(a: RiskAssessment) -> Alert:
    cat_label = a.category.value.lower()
    headline = (
        f"{a.level.value}: possible {cat_label} outbreak in {a.district_name} "
        f"(risk {a.risk_score:.0f}/100)"
    )
    reasons = [f"{c.label} {c.detail}" if c.detail else c.label for c in a.contributions[:5]]
    if a.likely_diseases:
        reasons.append("Most likely: " + ", ".join(a.likely_diseases[:3]))

    actions = [LEVEL_ACTIONS[a.level]] + ACTIONS_BY_CATEGORY.get(a.category, [])

    raw_id = f"{a.district_id}:{a.date.isoformat()}:{a.level.value}"
    alert_id = hashlib.sha1(raw_id.encode()).hexdigest()[:12]

    return Alert(
        id=alert_id,
        district_id=a.district_id,
        district_name=a.district_name,
        date=a.date,
        level=a.level,
        category=a.category,
        risk_score=a.risk_score,
        headline=headline,
        reasons=reasons,
        recommended_actions=actions,
        channels=CHANNELS_BY_LEVEL[a.level],
    )
