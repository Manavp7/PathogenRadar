from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.domain.models import SimulationRequest, SimulationResult
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes.dependencies import get_pipeline

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/district/{district_id}", response_model=SimulationResult)
def run_simulation(
    district_id: str,
    request: SimulationRequest,
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> SimulationResult:
    try:
        return pipeline.district_intelligence(district_id, request).simulation
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
