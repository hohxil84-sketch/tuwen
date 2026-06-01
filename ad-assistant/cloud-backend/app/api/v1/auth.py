"""Auth routes — login, refresh, logout.

See ``docs/auth-device-plan.md`` and ``docs/api-draft-auth-device.md``.
"""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.database import get_db
from app.schemas.auth import (
    LoginData,
    LoginRequest,
    LogoutData,
    LogoutRequest,
    RefreshData,
    RefreshRequest,
)
from app.schemas.common import error_response, success_response
from app.services.auth_service import login_user, logout_user, refresh_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=None,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login success — token pair returned"},
        401: {"description": "INVALID_CREDENTIALS"},
        403: {"description": "USER_DISABLED, DEVICE_LIMIT_REACHED"},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user and return access + refresh tokens.

    The access_token is short-lived (30 min) and kept in memory.
    The refresh_token (30 day, rotated on each use) is returned
    in plaintext ONLY in this response.
    """
    try:
        data = await login_user(
            db=db,
            account=body.account,
            password=body.password,
            device_fingerprint=body.device_fingerprint,
            ip_hash=_hash_ip(request),
        )
        return success_response(data=LoginData(**data).model_dump())
    except ValueError as exc:
        code = str(exc.args[0]) if exc.args else "UNKNOWN"
        return _auth_error(code)


@router.post(
    "/refresh",
    response_model=None,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "New token pair"},
        401: {"description": "REFRESH_INVALID, REFRESH_EXPIRED, TOKEN_REUSE"},
        403: {"description": "DEVICE_BANNED"},
    },
)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange a valid refresh_token for a new token pair.

    The old refresh_token is immediately revoked (token rotation).
    If a revoked token is replayed, ALL sessions for that user are revoked.
    """
    try:
        data = await refresh_access_token(
            db=db,
            refresh_token=body.refresh_token,
            device_fingerprint=body.device_fingerprint,
            ip_hash=_hash_ip(request),
        )
        return success_response(data=RefreshData(**data).model_dump())
    except ValueError as exc:
        code = str(exc.args[0]) if exc.args else "UNKNOWN"
        return _auth_error(code)


@router.post(
    "/logout",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def logout(
    body: LogoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Revoke the given refresh_token.

    Does NOT require a valid access_token — allows logout even when
    the access token is expired.
    """
    data = await logout_user(db=db, refresh_token=body.refresh_token)
    return success_response(data=LogoutData(**data).model_dump())


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _hash_ip(request: Request) -> str | None:
    """Return a SHA-256 hash of the client IP for privacy-preserving audit."""
    ip = request.client.host if request.client else None
    if ip is None:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()


def _auth_error(code: str):
    """Map internal ValueError codes to HTTP status codes and return JSONResponse."""
    mapping: dict[str, int] = {
        ErrorCode.INVALID_CREDENTIALS: 401,
        ErrorCode.REFRESH_INVALID: 401,
        ErrorCode.REFRESH_EXPIRED: 401,
        ErrorCode.TOKEN_REUSE: 401,
        ErrorCode.USER_DISABLED: 403,
        ErrorCode.DEVICE_BANNED: 403,
        ErrorCode.DEVICE_LIMIT_REACHED: 403,
        ErrorCode.DEVICE_NOT_BOUND: 403,
    }
    http_status = mapping.get(code, 400)
    body = error_response(code=code, message=_human_message(code))
    return JSONResponse(status_code=http_status, content=body.model_dump())


def _human_message(code: str) -> str:
    """Return a user-facing message for each error code."""
    messages = {
        ErrorCode.INVALID_CREDENTIALS: "Invalid account or password",
        ErrorCode.REFRESH_INVALID: "Refresh token is invalid or has been revoked",
        ErrorCode.REFRESH_EXPIRED: "Refresh token has expired, please login again",
        ErrorCode.TOKEN_REUSE: "Security alert: token replay detected, all sessions revoked",
        ErrorCode.USER_DISABLED: "Account is disabled",
        ErrorCode.DEVICE_BANNED: "Device is banned",
        ErrorCode.DEVICE_LIMIT_REACHED: "Maximum device limit reached",
        ErrorCode.DEVICE_NOT_BOUND: "Device is not bound to this account",
    }
    return messages.get(code, code)
