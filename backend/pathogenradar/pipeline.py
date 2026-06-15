"""End-to-end pipeline orchestration — the platform "tick".

Runs the full loop: acquire → quality → features → detect → fuse/classify → forecast → alert,
and persists artifacts the API/dashboard consume. This is the deterministic spine that turns
raw signals into executive-ready intelligence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from .acquisition.service import acquire
from .acquisition.synthetic import OutbreakEvent, dengue_outbreak
from .alerting.engine import generate_alerts
from .detection.engine import assess, latest_by_district
from .domain.models import Alert, DistrictForecast, RiskAssessment
from .features.pipeline import aggregate_sources
from .forecast.service import forecast_from_assessments
from .quality.engine import QualityResult
from .quality.engine import assess as assess_quality
from .regions import get_region_name
from .signals.service import run_detectors, scores_to_frame
from .store import repo

logger = logging.getLogger("pathogenradar.pipeline")

DEFAULT_DAYS = 180


@dataclass
class PipelineResult:
    region: str
    start: date
    end: date
    as_of: date
    assessments: list[RiskAssessment]
    forecasts: list[DistrictForecast]
    alerts: list[Alert]
    quality: QualityResult
    source_summary: dict[str, str]
    agg_df: pd.DataFrame
    signal_scores_df: pd.DataFrame
    risk_timeseries: pd.DataFrame


def run_pipeline(
    start: date | None = None,
    end: date | None = None,
    outbreaks: list[OutbreakEvent] | None = None,
    persist: bool = True,
) -> PipelineResult:
    end = end or date.today()
    start = start or (end - timedelta(days=DEFAULT_DAYS))
    logger.info("pipeline run %s..%s outbreaks=%d", start, end, len(outbreaks or []))

    # 1. Acquire (synthetic + any enabled real connectors)
    acq = acquire(start, end, outbreaks=outbreaks)
    raw = repo.signals_to_frame(acq.records)

    # 2. Data quality + confidence
    quality = assess_quality(raw)
    conf_by_day = {(r.district_id, r.date): r.confidence for r in quality.reports}

    # 3. Features (reliability-weighted multi-source aggregation)
    agg = aggregate_sources(raw, quality.source_reliability)

    # 4. Signal intelligence (per-source anomaly detection)
    scores = run_detectors(agg)
    scores_df = scores_to_frame(scores)

    # 5. Fusion + outbreak detection + explainability
    assessments = assess(scores, agg, conf_by_day)

    # 6. Deterministic spread forecast
    forecasts = forecast_from_assessments(assessments)

    # 7. Alerting (latest per district)
    latest = list(latest_by_district(assessments).values())
    alerts = generate_alerts(latest)

    risk_ts = _risk_timeseries(assessments)

    result = PipelineResult(
        region=get_region_name(),
        start=start,
        end=end,
        as_of=end,
        assessments=assessments,
        forecasts=forecasts,
        alerts=alerts,
        quality=quality,
        source_summary=acq.source_summary,
        agg_df=agg,
        signal_scores_df=scores_df,
        risk_timeseries=risk_ts,
    )

    if persist:
        _persist(result, raw)
    return result


def golden_scenario(
    district_id: str = "ernakulam",
    as_of: date | None = None,
    magnitude: float = 2.4,
    persist: bool = True,
) -> PipelineResult:
    """The flagship demo: a sharp, recent dengue outbreak peaking near 'now'.

    Tuned so the latest day reads as an active emergency: a fast 32-day outbreak whose peak
    (~12 days in) lands close to the current date, standing out clearly against the trailing
    surveillance baseline.
    """
    end = as_of or date.today()
    start = end - timedelta(days=DEFAULT_DAYS)
    outbreak_start = end - timedelta(days=14)
    outbreak = dengue_outbreak(
        district_id,
        outbreak_start,
        magnitude=magnitude,
        duration_days=32,
        peak_day_offset=12,
    )
    return run_pipeline(start, end, outbreaks=[outbreak], persist=persist)


def _risk_timeseries(assessments: list[RiskAssessment]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "district_id": a.district_id,
                "date": pd.Timestamp(a.date),
                "risk_score": a.risk_score,
                "level": a.level.value,
                "category": a.category.value,
                "confidence": a.confidence,
            }
            for a in assessments
        ]
    )


def _persist(result: PipelineResult, raw: pd.DataFrame) -> None:
    repo.write_signals(raw)
    repo.write_frame(result.risk_timeseries, repo.RISK_PARQUET)
    if not result.signal_scores_df.empty:
        repo.write_frame(result.signal_scores_df, "signal_scores.parquet")

    latest = list(latest_by_district(result.assessments).values())
    latest.sort(key=lambda a: a.risk_score, reverse=True)
    repo.write_json([a.model_dump(mode="json") for a in latest], "risk_latest.json")
    repo.write_json([f.model_dump(mode="json") for f in result.forecasts], "forecasts.json")
    repo.write_json([al.model_dump(mode="json") for al in result.alerts], repo.ALERTS_JSON)
    repo.write_json(
        {sid: s.model_dump(mode="json") for sid, s in result.quality.source_reliability.items()},
        "sources.json",
    )
    repo.write_json(
        {
            "region": result.region,
            "start": result.start.isoformat(),
            "end": result.end.isoformat(),
            "as_of": result.as_of.isoformat(),
            "source_summary": result.source_summary,
        },
        "meta.json",
    )
    logger.info("persisted pipeline artifacts to %s", repo.SEED_DIR)
