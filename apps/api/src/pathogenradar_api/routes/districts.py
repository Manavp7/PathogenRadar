from fastapi import APIRouter, Depends, HTTPException

from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import District
from pathogenradar_api.routes.dependencies import get_repository

router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("", response_model=list[District])
def list_districts(repository: DemoRepository = Depends(get_repository)) -> list[District]:
    return list(repository.list_districts())


@router.get("/{district_id}", response_model=District)
def get_district(
    district_id: str, repository: DemoRepository = Depends(get_repository)
) -> District:
    try:
        return repository.get_district(district_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="District not found") from exc
