"""Raw signal timeseries endpoint (for the district signal-breakdown charts)."""

from __future__ import annotations

from fastapi import APIRouter

from .state import state

router = APIRouter(prefix="/api", tags=["signals"])


@router.get("/signals/{district_id}")
def get_signals(district_id: str) -> dict:
    df = state.signals
    if df.empty:
        return {"district_id": district_id, "series": {}}
    sub = df[df["district_id"] == district_id]
    # Aggregate across sources (mean) per date/signal for display.
    series: dict[str, list[dict]] = {}
    for signal_type, grp in sub.groupby("signal_type"):
        daily = grp.groupby("date")["value"].mean().sort_index()
        series[signal_type] = [
            {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 3)} for d, v in daily.items()
        ]
    return {"district_id": district_id, "series": series}
