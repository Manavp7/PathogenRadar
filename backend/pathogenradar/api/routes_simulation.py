"""On-demand SEIR simulation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..domain.models import Intervention, SeirResult
from ..knowledge import get_knowledge_graph
from ..simulation.seir import simulate

router = APIRouter(prefix="/api", tags=["simulation"])


class SimulationRequest(BaseModel):
    district_id: str
    disease: str = "dengue"
    days: int = Field(default=160, ge=30, le=365)
    initial_infected: float | None = None
    intervention: Intervention = Field(default_factory=Intervention)


@router.post("/simulation", response_model=SeirResult)
def run_simulation(req: SimulationRequest, region: str | None = Query(default=None)) -> SeirResult:
    kg = get_knowledge_graph()
    if req.disease not in kg.diseases():
        raise HTTPException(status_code=400, detail=f"Unknown disease '{req.disease}'")
    try:
        return simulate(
            district_id=req.district_id,
            disease=req.disease,
            intervention=req.intervention,
            days=req.days,
            initial_infected=req.initial_infected,
            kg=kg,
            region=region,
        )
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Unknown district '{req.district_id}'"
        ) from None


@router.get("/diseases")
def list_diseases() -> list[dict]:
    kg = get_knowledge_graph()
    return [
        {"id": d, "name": kg.display_name(d), "category": kg.category_for(d).value}
        for d in kg.diseases()
    ]
