"""Genomic surveillance endpoint (synthetic variant frequencies + emerging detection)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from ..genomics import (
    DENGUE_VARIANTS,
    current_shares,
    detect_emerging,
    r0_multiplier,
    severity_multiplier,
    variant_frequencies,
)
from .deps import region_state
from .state import RegionState

router = APIRouter(prefix="/api", tags=["genomics"])


@router.get("/genomics")
def get_genomics(rs: RegionState = Depends(region_state)) -> dict:
    as_of_raw = rs.meta.get("as_of")
    as_of = date.fromisoformat(as_of_raw) if as_of_raw else date.today()
    dates, shares = variant_frequencies(rs.key, days=120, as_of=as_of)
    now = current_shares(shares)
    emerging = detect_emerging(shares)
    vmap = {v.id: v for v in DENGUE_VARIANTS}

    return {
        "region": rs.meta.get("region", rs.key),
        "note": "synthetic variant surveillance (demonstration)",
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "transmissibility": v.transmissibility,
                "severity": v.severity,
            }
            for v in DENGUE_VARIANTS
        ],
        "dates": [d.strftime("%Y-%m-%d") for d in dates],
        "series": {vid: [round(x, 4) for x in s] for vid, s in shares.items()},
        "current_mix": [
            {"id": vid, "name": vmap[vid].name, "share": round(share, 4)}
            for vid, share in sorted(now.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "emerging": [{**e, "name": vmap[e["variant"]].name} for e in emerging],
        "r0_multiplier": round(r0_multiplier(now), 4),
        "severity_multiplier": round(severity_multiplier(now), 4),
    }
