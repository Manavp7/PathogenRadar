"""Consistent error envelope for the API.

Every error response has the shape ``{"error": {"code": <int>, "message": <str>, ...}}`` so
clients can handle failures uniformly.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("pathogenradar.api.errors")


def _envelope(code: int, message: str, **extra) -> dict:
    return {"error": {"code": code, "message": message, **extra}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(_: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code, content=_envelope(exc.status_code, str(exc.detail))
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(_: Request, exc: RequestValidationError):
        details = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", "")} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_envelope(422, "Validation error", details=details),
        )

    @app.exception_handler(Exception)
    async def _unhandled_exc(_: Request, exc: Exception):  # pragma: no cover - safety net
        logger.exception("unhandled error: %s", exc)
        return JSONResponse(status_code=500, content=_envelope(500, "Internal server error"))
