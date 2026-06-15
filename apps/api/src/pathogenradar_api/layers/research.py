from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import ResearchQuery, ResearchResult


class ResearchModeService:
    """Safe predefined demo research queries."""

    def __init__(self, repository: DemoRepository) -> None:
        self.repository = repository

    def query(self, request: ResearchQuery) -> ResearchResult:
        if request.query_type == "historical_outbreaks":
            return ResearchResult(
                query_type=request.query_type,
                title="Synthetic historical outbreak analogs",
                rows=[
                    {"year": 2018, "state": "Kerala", "pattern": "vector", "peak_week": 28},
                    {"year": 2020, "state": "Maharashtra", "pattern": "respiratory", "peak_week": 17},
                    {"year": 2023, "state": "Maharashtra", "pattern": "waterborne", "peak_week": 30},
                ],
                caveats=["Illustrative rows only; not real historical surveillance data."],
            )
        if request.query_type == "source_reliability":
            rows = [
                {"source": "hospital", "demo_reliability": 0.91},
                {"source": "wastewater", "demo_reliability": 0.86},
                {"source": "search", "demo_reliability": 0.78},
                {"source": "social", "demo_reliability": 0.71},
            ]
            return ResearchResult(
                query_type=request.query_type,
                title="Demo source reliability ranking",
                rows=rows,
                caveats=["Reliability is computed from fixture quality, not source contracts."],
            )
        if request.query_type == "forecast_comparison":
            districts = self.repository.list_districts()
            return ResearchResult(
                query_type=request.query_type,
                title="Demo districts available for forecast comparison",
                rows=[{"district_id": district.id, "state": district.state} for district in districts],
                caveats=["Use forecast endpoints for deterministic scenario output."],
            )
        return ResearchResult(
            query_type=request.query_type,
            title="Unsupported demo query",
            rows=[],
            caveats=["Allowed query_type values: historical_outbreaks, source_reliability, forecast_comparison."],
        )
