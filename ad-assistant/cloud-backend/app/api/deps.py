"""FastAPI dependencies — authentication and authorisation.

Implements the **6-step auth verification chain** from the confirmed plan:

1. Extract & validate access_token (JWT signature + expiry)
2. Check user status (users.status == 'active')
3. Verify device binding (device belongs to user)
4. Check device status (devices.status == 'active', not banned)
5. Validate plan (plan_code is valid)
6. Check feature permission (feature in allowed list)

Each step returns the appropriate HTTP error on failure.
"""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.security import decode_access_token
from app.database import get_db
from app.models.device import Device
from app.models.user import User


async def get_access_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract Bearer token from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTH_REQUIRED, "message": "Authentication required"},
        )
    return authorization.removeprefix("Bearer ").strip()


async def get_current_user_payload(
    token: Annotated[str, Depends(get_access_token)],
) -> dict:
    """Step 1: Validate JWT signature and expiry. Returns decoded payload."""
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_EXPIRED, "message": "Access token expired"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTH_REQUIRED, "message": "Invalid access token"},
        )
    return payload


async def get_current_user(
    payload: Annotated[dict, Depends(get_current_user_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Step 2: Verify user exists and is active."""
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTH_REQUIRED, "message": "Invalid token payload"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTH_REQUIRED, "message": "Invalid token payload"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTH_REQUIRED, "message": "User not found"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.USER_DISABLED, "message": "User account is disabled"},
        )

    return user


async def get_current_device(
    user: Annotated[User, Depends(get_current_user)],
    payload: Annotated[dict, Depends(get_current_user_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Device:
    """Step 3 + 4: Verify device belongs to user AND is not banned."""
    device_id_str = payload.get("device_id")
    if not device_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.DEVICE_NOT_BOUND, "message": "Device ID missing in token"},
        )

    try:
        device_id = uuid.UUID(device_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.DEVICE_NOT_BOUND, "message": "Device not found"},
        )

    result = await db.execute(select(Device).where(Device.id == device_id))
    device: Device | None = result.scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.DEVICE_NOT_BOUND, "message": "Device not found"},
        )

    if str(device.user_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.DEVICE_NOT_BOUND, "message": "Device not bound to this user"},
        )

    if device.status == "banned":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.DEVICE_BANNED, "message": "Device is banned"},
        )

    return device


async def get_current_user_with_device(
    user: Annotated[User, Depends(get_current_user)],
    device: Annotated[Device, Depends(get_current_device)],
) -> tuple[User, Device]:
    """Combined dependency returning (user, device) after steps 1-4.

    Steps 5 (plan validity) and 6 (feature permission) are checked at the
    route level because they depend on the specific endpoint.
    """
    return user, device


# ---------------------------------------------------------------------------
# Plan & feature checks (called from route handlers as needed)
# ---------------------------------------------------------------------------

# NOTE: Must stay in sync with active plan codes in the ``plans`` table.
# Used as a fast in-process guard (no DB query per request). When adding
# new plans via seed data / admin, update this set accordingly.
VALID_PLANS = frozenset({"standard", "expert", "enterprise"})


def verify_plan(user: User) -> None:
    """Step 5: Raise 403 if user's plan_code is not valid."""
    if user.plan_code not in VALID_PLANS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PLAN_INVALID, "message": "Plan is invalid or expired"},
        )


# Map feature → allowed plan (used by step 6 when feature-specific routes are added)
FEATURE_PLAN_REQUIREMENTS: dict[str, set[str]] = {
    # OCR is available on all plans
    "ocr": {"standard", "expert", "enterprise"},
    # Mock AI ad-copy — Sprint-02 Task-04
    "mock_ad_copy": {"standard", "expert", "enterprise"},
}


def verify_feature(user: User, feature: str) -> None:
    """Step 6: Raise 403 if feature is not allowed for user's plan.

    ⚠️ This is a runtime check against the database (not the JWT plan claim).
    """
    allowed = FEATURE_PLAN_REQUIREMENTS.get(feature)
    if allowed is None:
        # Unknown feature — deny by default
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FEATURE_NOT_ALLOWED,
                "message": f"Feature '{feature}' is not recognised",
            },
        )
    if user.plan_code not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FEATURE_NOT_ALLOWED,
                "message": f"Feature '{feature}' requires a higher plan",
            },
        )


# ---------------------------------------------------------------------------
# RBAC — Role-Based Access Control (S05-R03)
# ---------------------------------------------------------------------------

# Role → permission mapping.  Unknown roles default to empty set (deny all).
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "users:read",
        "orders:read",
        "credits:grant",
        "provider_logs:read",
        "usage_events:read",
    },
    "operator": {
        "users:read",
        "orders:read",
        "provider_logs:read",
        "usage_events:read",
    },
    # "user" has no admin permissions — default deny
}


class PermissionChecker:
    """FastAPI dependency — require a specific admin permission.

    Checks the authenticated user's ``role`` against ``ROLE_PERMISSIONS``.
    Falls back to ``ADMIN_USER_IDS`` for bootstrap when no role grants the
    permission yet (allows seeding the first admin without direct DB access).

    Usage::

        @router.get("/users")
        async def admin_list_users(
            admin: Annotated[User, Depends(PermissionChecker("users:read"))],
            ...
        ):
    """

    def __init__(self, permission: str) -> None:
        self.permission = permission

    async def __call__(
        self,
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        # 1) Role-based check (primary)
        allowed = ROLE_PERMISSIONS.get(user.role, set())
        if self.permission in allowed:
            return user

        # 2) Bootstrap fallback — ADMIN_USER_IDS whitelist
        admin_ids: set[str] = set(settings.ADMIN_USER_IDS)
        if str(user.id) in admin_ids:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Admin access required",
            },
        )


# ---------------------------------------------------------------------------
# Deprecated — kept for backward reference only
# ---------------------------------------------------------------------------
# The `get_admin_user` function was removed in S05-R03 in favor of
# `PermissionChecker`, which performs fine-grained permission checks.
# All admin endpoints now use PermissionChecker("permission_name").
