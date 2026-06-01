"""Unified API response wrapper.

Provides a generic ``APIResponse[T]`` model and helper factories so that
FastAPI endpoints can declare typed ``response_model`` while keeping a
single unified response envelope.

``APIResponse[SomeSchema]`` is the canonical way to wire a typed response
on an endpoint.  The ``success_response()`` / ``error_response()`` helpers
still work for callers that donʼt wire a typed ``response_model``.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class APIResponse(BaseModel, Generic[T]):
    """Generic unified API response envelope.

    Usage::

        @router.post("/endpoint", response_model=APIResponse[SomeSchema])
        async def endpoint(...) -> APIResponse[SomeSchema]:
            ...
    """

    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    request_id: str | None = None


def success_response(
    data: Any = None, request_id: str | None = None
) -> APIResponse[Any]:
    """Build a successful response.

    ``data`` may be a plain dict, a Pydantic model instance, or any
    JSON-serialisable value.  When an endpoint wires a typed
    ``response_model`` (e.g. ``response_model=APIResponse[MockAdCopyData]``),
    pass the Pydantic model instance directly — FastAPI serialises it
    through the declared ``response_model``.
    """
    return APIResponse[Any](success=True, data=data, request_id=request_id)


def error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> APIResponse[Any]:
    """Build an error response."""
    return APIResponse[Any](
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        request_id=request_id,
    )
