from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.domain.models import ExecutiveReport
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes.dependencies import get_pipeline

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/executive", response_model=ExecutiveReport)
def executive_report(
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> ExecutiveReport:
    national = pipeline.national_intelligence()
    return national.districts[0].report


@router.get("/district/{district_id}", response_model=ExecutiveReport)
def district_report(
    district_id: str,
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> ExecutiveReport:
    try:
        return pipeline.district_intelligence(district_id).report
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
