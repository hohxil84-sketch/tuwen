"""Cloud Backend FastAPI Application — Sprint-01 Auth/Device implementation."""

import uuid as _uuid
import time as _time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.common import error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup checks.

    Refuses to start if JWT_SECRET_KEY is still the default placeholder
    (security requirement from ``docs/auth-device-plan.md`` §8).
    """
    if settings.JWT_SECRET_KEY == "change-me-in-production-use-env-var":
        raise RuntimeError(
            "JWT_SECRET_KEY is still the default placeholder. "
            "Set the JWT_SECRET_KEY environment variable before starting the server."
        )
    yield


app = FastAPI(
    title="AI 图文广告助手 Cloud Backend",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handler — wrap HTTPException in unified error format
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert all HTTPExceptions to the unified ``{success, data, error, request_id}``
    format defined in ``docs/05-api-contract.md``.

    Dependencies (``deps.py``) raise ``HTTPException(detail={...})`` with
    ``code`` / ``message`` keys — these are normalised here.
    """
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "UNKNOWN")
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("details")
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(exc.detail) if exc.detail else ""
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=code, message=message, details=details).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors (422) to the unified
    ``{success, data, error, request_id}`` format.
    """
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        details.append({
            "loc": list(err["loc"]),
            "msg": err["msg"],
            "type": err["type"],
        })

    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": details},
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Middleware — request ID injection
# ---------------------------------------------------------------------------


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Inject a unique request_id into every JSON response."""
    rid = request.headers.get("X-Request-ID") or f"req_{_uuid.uuid4().hex[:12]}"
    start = _time.perf_counter()

    response = await call_next(request)

    # Inject into JSON body if possible
    if response.headers.get("content-type") == "application/json":
        import json

        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        try:
            body = json.loads(body_bytes)
            body["request_id"] = rid
            response = JSONResponse(content=body, status_code=response.status_code)
        except (json.JSONDecodeError, TypeError):
            response = JSONResponse(
                content=body_bytes.decode("utf-8", errors="replace"),
                status_code=response.status_code,
            )
    else:
        response.headers["X-Request-ID"] = rid

    response.headers["X-Response-Time-ms"] = f"{(_time.perf_counter() - start) * 1000:.1f}"
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.api.v1.auth import router as auth_router
from app.api.v1.devices import router as devices_router

app.include_router(auth_router)
app.include_router(devices_router)


@app.get("/health")
async def health():
    return {"status": "ok", "sprint": "01", "mode": "auth-device"}
