from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.domain.models import DistrictIntelligence, NationalIntelligence
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes.dependencies import get_pipeline

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/national", response_model=NationalIntelligence)
def national_intelligence(
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> NationalIntelligence:
    return pipeline.national_intelligence()


@router.get("/district/{district_id}", response_model=DistrictIntelligence)
def district_intelligence(
    district_id: str,
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> DistrictIntelligence:
    try:
        return pipeline.district_intelligence(district_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
