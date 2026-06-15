from fastapi import Request

from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.layers.pipeline import IntelligencePipeline


def get_repository(request: Request) -> DemoRepository:
    return request.app.state.repository


def get_pipeline(request: Request) -> IntelligencePipeline:
    return request.app.state.pipeline
