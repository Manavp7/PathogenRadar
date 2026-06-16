"""PathogenRadar FastAPI application.

Serves the disease-intelligence pipeline outputs (risk, forecast, alerts, simulation,
briefings) to the React dashboard. Optional API-key auth; audit logging on every request.
"""

from __future__ import annotations

import logging
import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__
from ..security.auth import audit_logger, require_api_key
from . import (
    routes_alerts,
    routes_districts,
    routes_forecast,
    routes_reports,
    routes_risk,
    routes_signals,
    routes_simulation,
    routes_system,
)
from .errors import register_exception_handlers
from .state import state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pathogenradar.api")

app = FastAPI(
    title="PathogenRadar API",
    version=__version__,
    description="A government-grade disease-intelligence platform (Phase 1 MVP — Kerala).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    started = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - started) * 1000
    audit_logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.on_event("startup")
def _startup() -> None:
    from ..config import get_settings

    for warning in get_settings().warnings():
        logger.warning("config: %s", warning)
    state.ensure_seed()
    logger.info("PathogenRadar API ready (region=%s)", state.meta.get("region"))


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "version": __version__, "region": state.meta.get("region")}


# All data routes require the API key when one is configured.
_auth = [Depends(require_api_key)]
app.include_router(routes_districts.router, dependencies=_auth)
app.include_router(routes_risk.router, dependencies=_auth)
app.include_router(routes_forecast.router, dependencies=_auth)
app.include_router(routes_alerts.router, dependencies=_auth)
app.include_router(routes_simulation.router, dependencies=_auth)
app.include_router(routes_signals.router, dependencies=_auth)
app.include_router(routes_reports.router, dependencies=_auth)
app.include_router(routes_system.router, dependencies=_auth)
