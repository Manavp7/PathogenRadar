from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathogenradar_api.core.config import get_settings
from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.layers.pipeline import IntelligencePipeline
from pathogenradar_api.routes import alerts, districts, forecasts, health, intelligence, reports, research, simulations


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Demo disease intelligence API using synthetic data. "
            "Not for clinical or emergency use."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    repository = DemoRepository()
    app.state.repository = repository
    app.state.pipeline = IntelligencePipeline(repository)

    app.include_router(health.router)
    app.include_router(districts.router)
    app.include_router(intelligence.router)
    app.include_router(forecasts.router)
    app.include_router(simulations.router)
    app.include_router(reports.router)
    app.include_router(alerts.router)
    app.include_router(research.router)
    return app


app = create_app()
