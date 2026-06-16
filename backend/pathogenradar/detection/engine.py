"""Outbreak detection engine.

Fuses detector scores into a risk score, classifies the outbreak level, infers the most
likely disease category via the knowledge graph, and produces an explainable contribution
breakdown — all deterministic / statistical (no LLM).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import numpy as np
import pandas as pd

from ..domain.models import DiseaseCategory, RiskAssessment, SignalScore, SignalType
from ..explain.contributions import build_contributions
from ..fusion.fuser import risk_score
from ..knowledge import KnowledgeGraphRepo, get_knowledge_graph
from ..regions import get_district_map
from .classifier import level_for
from .novelty import get_novelty_detector

VALID_SIGNALS = {s.value for s in SignalType}
NOVELTY_MIN_RISK = 55.0  # only consider novelty at Alert+ severity
NOVELTY_FLAG = 0.6  # novelty above this => candidate novel pathogen
WEAK_MATCH_NOVEL = 0.85  # lenient: novelty is the primary discriminator, not the KG match
WEATHER_TYPES = {
    "weather_rainfall": "rainfall",
    "weather_humidity": "humidity",
    "weather_temp": "temp",
}
WATCH_MIN = 15.0


def assess(
    signal_scores: list[SignalScore],
    agg_df: pd.DataFrame,
    confidence_by_day: dict[tuple[str, date], float] | None = None,
    kg: KnowledgeGraphRepo | None = None,
    region: str | None = None,
) -> list[RiskAssessment]:
    kg = kg or get_knowledge_graph()
    confidence_by_day = confidence_by_day or {}
    names = get_district_map(region)
    novelty_detector = get_novelty_detector()

    grouped = _group_scores(signal_scores)
    pct_lookup, weather_lookup = _context(agg_df)

    assessments: list[RiskAssessment] = []
    for (district_id, day), info in grouped.items():
        confidence = confidence_by_day.get((district_id, day), 1.0)
        risk = risk_score(info["detectors"], confidence)
        level = level_for(risk)

        drivers = info["drivers"]  # signal -> anomaly (0..1), incl. multivariate_context
        elevated = {sig: a for sig, a in drivers.items() if a > 0.05 and sig in VALID_SIGNALS}
        weather_state = weather_lookup.get((district_id, day), {})

        category = DiseaseCategory.UNKNOWN
        likely: list[str] = []
        best_match = 0.0
        if risk >= WATCH_MIN and elevated:
            matches = kg.match_diseases(elevated, weather_state, top_k=3)
            if matches:
                best_match = matches[0].score
                category = matches[0].category
                likely = [m.display_name for m in matches]

        # Novel-pathogen detection: a high-risk pattern that the novelty model finds unlike
        # any known disease (the novelty gate already protects genuine known presentations).
        novelty = novelty_detector.score(elevated) if (risk >= WATCH_MIN and elevated) else 0.0
        novel = (
            risk >= NOVELTY_MIN_RISK and novelty >= NOVELTY_FLAG and best_match < WEAK_MATCH_NOVEL
        )
        if novel:
            category = DiseaseCategory.UNKNOWN
            likely = []

        pct = pct_lookup.get((district_id, day), {})
        contributions = (
            build_contributions(pct, drivers, weather_state) if risk >= WATCH_MIN else []
        )

        district = names.get(district_id)
        assessments.append(
            RiskAssessment(
                district_id=district_id,
                district_name=district.name if district else district_id,
                date=day,
                risk_score=risk,
                level=level,
                category=category,
                likely_diseases=likely,
                confidence=round(confidence, 4),
                signal_scores={k: round(v, 4) for k, v in info["detectors"].items()},
                contributions=contributions,
                novelty_score=round(novelty, 4),
                novel_pathogen=novel,
            )
        )
    return assessments


def latest_by_district(assessments: list[RiskAssessment]) -> dict[str, RiskAssessment]:
    latest: dict[str, RiskAssessment] = {}
    for a in assessments:
        cur = latest.get(a.district_id)
        if cur is None or a.date > cur.date:
            latest[a.district_id] = a
    return latest


# --------------------------------------------------------------------------------------
# Internals
# --------------------------------------------------------------------------------------


def _group_scores(signal_scores: list[SignalScore]) -> dict:
    grouped: dict = defaultdict(lambda: {"detectors": {}, "drivers": {}})
    for s in signal_scores:
        key = (s.district_id, s.date)
        grouped[key]["detectors"][s.detector] = s.score
        for sig, anom in s.drivers.items():
            cur = grouped[key]["drivers"].get(sig, 0.0)
            grouped[key]["drivers"][sig] = max(cur, anom)
    return grouped


def _context(agg_df: pd.DataFrame, window: int = 42):
    """Return (pct_change_lookup, weather_state_lookup) keyed by (district_id, date)."""
    pct_lookup: dict[tuple[str, date], dict[str, float]] = defaultdict(dict)
    weather_lookup: dict[tuple[str, date], dict[str, str]] = defaultdict(dict)
    if agg_df.empty:
        return pct_lookup, weather_lookup

    df = agg_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["district_id", "signal_type", "date"])
    df["baseline"] = df.groupby(["district_id", "signal_type"])["value"].transform(
        lambda s: s.shift(1).rolling(window, min_periods=10).median()
    )
    denom = df["baseline"].abs().replace(0, np.nan)
    df["pct"] = (df["value"] - df["baseline"]) / denom * 100.0

    for r in df.itertuples():
        d = r.date.date()
        if pd.notna(r.pct):
            pct_lookup[(r.district_id, d)][r.signal_type] = float(r.pct)

    weather = df[df["signal_type"].isin(WEATHER_TYPES)]
    for (_district_id, stype), grp in weather.groupby(["district_id", "signal_type"], sort=False):
        hi = grp["value"].quantile(0.7)
        lo = grp["value"].quantile(0.3)
        key = WEATHER_TYPES[stype]
        for r in grp.itertuples():
            state = "high" if r.value >= hi else ("low" if r.value <= lo else "normal")
            weather_lookup[(r.district_id, r.date.date())][key] = state

    return pct_lookup, weather_lookup
