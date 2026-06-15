"""Briefing assembly: build a structured context from pipeline outputs and render it."""

from __future__ import annotations

from datetime import date

from ..alerting.engine import ACTIONS_BY_CATEGORY, LEVEL_ACTIONS
from ..domain.models import Briefing, DiseaseCategory, OutbreakLevel
from . import BriefingContext, get_briefing_provider

NON_NORMAL = {
    OutbreakLevel.WATCH.value,
    OutbreakLevel.WARNING.value,
    OutbreakLevel.ALERT.value,
    OutbreakLevel.EMERGENCY.value,
}


def build_context(
    region: str,
    as_of: date,
    risk_latest: list[dict],
    forecasts: list[dict],
    source_summary: dict[str, str] | None = None,
) -> BriefingContext:
    on_alert = [r for r in risk_latest if r.get("level") in NON_NORMAL]
    top = sorted(risk_latest, key=lambda r: r.get("risk_score", 0), reverse=True)[:5]
    top_districts = [
        {
            "name": r["district_name"],
            "risk": float(r.get("risk_score", 0)),
            "level": r.get("level"),
            "category": r.get("category"),
            "diseases": r.get("likely_diseases", []),
        }
        for r in top
        if r.get("level") in NON_NORMAL
    ]

    # Forecast highlights: districts (excluding current hotspots) with the highest 30-day rise.
    hotspots = {r["district_id"] for r in on_alert}
    fh = []
    for f in forecasts:
        if f["district_id"] in hotspots:
            continue
        p30 = f["points"][-1]["risk_probability"] if f.get("points") else 0.0
        fh.append({"name": f["district_name"], "prob_30d": p30})
    fh = sorted(fh, key=lambda x: x["prob_30d"], reverse=True)[:4]

    actions = _recommended_actions(top_districts)

    return BriefingContext(
        region=region,
        as_of=as_of,
        total_districts=len(risk_latest),
        districts_on_alert=len(on_alert),
        top_districts=top_districts,
        forecast_highlights=fh,
        recommended_actions=actions,
        data_sources=source_summary or {},
    )


def _recommended_actions(top_districts: list[dict]) -> list[str]:
    if not top_districts:
        return ["Maintain routine surveillance and weekly signal review."]
    lead = top_districts[0]
    actions: list[str] = []
    try:
        level = OutbreakLevel(lead["level"])
        actions.append(LEVEL_ACTIONS[level])
    except (ValueError, KeyError):
        pass
    try:
        category = DiseaseCategory(lead.get("category"))
    except (ValueError, TypeError):
        category = DiseaseCategory.UNKNOWN
    actions.extend(ACTIONS_BY_CATEGORY.get(category, [])[:2])
    return actions


def generate_briefing(
    region: str,
    as_of: date,
    risk_latest: list[dict],
    forecasts: list[dict],
    source_summary: dict[str, str] | None = None,
) -> Briefing:
    context = build_context(region, as_of, risk_latest, forecasts, source_summary)
    provider = get_briefing_provider()
    body = provider.render(context)
    title = f"{region} Health Intelligence Briefing — {as_of.isoformat()}"
    return Briefing(
        region=region,
        date=as_of,
        provider=provider.name,
        title=title,
        body=body,
    )
