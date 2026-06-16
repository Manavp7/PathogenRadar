"""Risk endpoints: latest risk per district + per-district detail with timeseries."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from ..regions import get_district_map
from .pagination import paginate
from .state import state

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/risk")
def get_risk(
    as_of: str | None = Query(default=None, description="Historical snapshot date YYYY-MM-DD"),
    limit: int | None = Query(default=None, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Latest risk per district, or a historical snapshot when ``as_of`` is supplied."""
    rows = _snapshot(as_of) if as_of else state.risk_latest
    return paginate(rows, limit, offset)


@router.get("/timeline")
def get_timeline() -> dict:
    """Available dates + the national risk index (mean/max across districts) per date."""
    ts = state.risk_ts
    if ts.empty:
        return {"dates": [], "series": []}
    g = ts.groupby("date")["risk_score"].agg(["mean", "max"]).reset_index().sort_values("date")
    series = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "mean": round(float(m), 2),
            "max": round(float(mx), 2),
        }
        for d, m, mx in zip(g["date"], g["mean"], g["max"], strict=False)
    ]
    return {"dates": [s["date"] for s in series], "series": series}


def _snapshot(as_of: str) -> list[dict]:
    ts = state.risk_ts
    if ts.empty:
        return []
    try:
        day = pd.Timestamp(as_of)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid date '{as_of}'") from exc
    sub = ts[ts["date"] == day]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No data for {as_of}")
    names = get_district_map()
    rows = [
        {
            "district_id": r.district_id,
            "district_name": names[r.district_id].name if r.district_id in names else r.district_id,
            "date": as_of,
            "risk_score": float(r.risk_score),
            "level": r.level,
            "category": r.category,
            "likely_diseases": [],
            "confidence": float(getattr(r, "confidence", 1.0)),
            "signal_scores": {},
            "contributions": [],
        }
        for r in sub.itertuples()
    ]
    rows.sort(key=lambda x: x["risk_score"], reverse=True)
    return rows


@router.get("/risk/{district_id}")
def get_risk_for_district(district_id: str) -> dict:
    latest = next((r for r in state.risk_latest if r["district_id"] == district_id), None)
    if latest is None:
        raise HTTPException(status_code=404, detail=f"Unknown district '{district_id}'")

    ts = state.risk_ts
    timeseries = []
    if not ts.empty:
        sub = ts[ts["district_id"] == district_id].sort_values("date")
        timeseries = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "risk_score": float(r),
                "level": lvl,
            }
            for d, r, lvl in zip(sub["date"], sub["risk_score"], sub["level"], strict=False)
        ]

    detectors = []
    ss = state.signal_scores
    if not ss.empty and district_id in set(ss["district_id"]):
        sub = ss[ss["district_id"] == district_id].sort_values("date")
        detector_cols = [c for c in sub.columns if c not in {"district_id", "date"}]
        detectors = [
            {"date": row["date"].strftime("%Y-%m-%d"), **{c: _f(row[c]) for c in detector_cols}}
            for _, row in sub.iterrows()
        ]

    return {"latest": latest, "timeseries": timeseries, "detectors": detectors}


def _f(v) -> float | None:
    try:
        if v != v:  # NaN
            return None
        return float(v)
    except (TypeError, ValueError):
        return None
