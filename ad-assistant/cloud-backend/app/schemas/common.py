"""Unified API response wrapper."""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class APIResponse(BaseModel):
    success: bool
    data: Any | None = None
    error: ErrorDetail | None = None
    request_id: str | None = None


def success_response(data: Any, request_id: str | None = None) -> APIResponse:
    return APIResponse(success=True, data=data, request_id=request_id)


def error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> APIResponse:
    return APIResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        request_id=request_id,
    )
