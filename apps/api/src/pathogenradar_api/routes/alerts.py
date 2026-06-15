from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.domain.models import Alert
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes.dependencies import get_pipeline

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
def list_alerts(pipeline: IntelligencePipeline = Depends(get_pipeline)) -> list[Alert]:
    national = pipeline.national_intelligence()
    return [district.alert for district in national.districts if district.alert is not None]


@router.get("/district/{district_id}", response_model=Alert | None)
def district_alert(
    district_id: str,
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> Alert | None:
    try:
        return pipeline.district_intelligence(district_id).alert
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
