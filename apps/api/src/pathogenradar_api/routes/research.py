from fastapi import APIRouter, Depends

from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import ResearchQuery, ResearchResult
from pathogenradar_api.layers.research import ResearchModeService
from pathogenradar_api.routes.dependencies import get_repository

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/query", response_model=ResearchResult)
def research_query(
    request: ResearchQuery,
    repository: DemoRepository = Depends(get_repository),
) -> ResearchResult:
    return ResearchModeService(repository).query(request)
