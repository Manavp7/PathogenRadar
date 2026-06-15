from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.domain.models import SpreadForecast
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes.dependencies import get_pipeline

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("/district/{district_id}", response_model=SpreadForecast)
def district_forecast(
    district_id: str,
    pipeline: IntelligencePipeline = Depends(get_pipeline),
) -> SpreadForecast:
    try:
        return pipeline.district_intelligence(district_id).forecast
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
