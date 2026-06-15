"""Risk endpoints: latest risk per district + per-district detail with timeseries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .state import state

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/risk")
def get_risk() -> list[dict]:
    """Latest risk assessment per district, sorted by risk (for the heatmap)."""
    return state.risk_latest


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
