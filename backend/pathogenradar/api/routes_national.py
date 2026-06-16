"""National roll-up across all loaded regions."""

from __future__ import annotations

from fastapi import APIRouter

from .state import state

router = APIRouter(prefix="/api", tags=["national"])

NON_NORMAL = {"Watch", "Warning", "Alert", "Emergency"}


@router.get("/national")
def get_national() -> dict:
    regions_summary = []
    all_hotspots = []
    total_districts = 0
    total_alerts = 0

    for key, rs in state.regions.items():
        risks = rs.risk_latest
        elevated = [r for r in risks if r.get("level") in NON_NORMAL]
        top = max(risks, key=lambda r: r.get("risk_score", 0), default=None)
        total_districts += len(risks)
        total_alerts += len(rs.alerts)
        regions_summary.append(
            {
                "key": key,
                "name": rs.meta.get("region", key),
                "districts": len(risks),
                "elevated": len(elevated),
                "alerts": len(rs.alerts),
                "top_district": top["district_name"] if top else None,
                "top_risk": round(top["risk_score"], 1) if top else 0.0,
                "as_of": rs.meta.get("as_of"),
            }
        )
        for r in elevated:
            all_hotspots.append(
                {
                    "region": rs.meta.get("region", key),
                    "district_name": r["district_name"],
                    "risk_score": r["risk_score"],
                    "level": r["level"],
                    "category": r.get("category"),
                }
            )

    all_hotspots.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "regions": sorted(regions_summary, key=lambda x: x["top_risk"], reverse=True),
        "totals": {
            "regions": len(state.regions),
            "districts": total_districts,
            "alerts": total_alerts,
            "elevated": len(all_hotspots),
        },
        "hotspots": all_hotspots[:10],
    }
