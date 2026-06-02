"""Admin API routes — 管理员操作（查询、赠送积分等）."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PermissionChecker
from app.database import get_db
from app.providers.circuit_breaker import get_circuit_breaker_registry
from app.models.user import User
from app.schemas.admin import (
    AdminGrantRequest,
    AdminGrantResponse,
    AdminCreditAccountItem,
    AdminOrderItem,
    AdminProviderLogItem,
    AdminUsageEventItem,
    AdminUserItem,
    MonthlyGrantRequest,
    MonthlyGrantResponse,
    PaginatedItems,
    ProviderHealthItem,
    ProviderHealthResponse,
)
from app.schemas.common import success_response
from app.services import admin_service
from app.services.credit_service import grant_credits
from app.services.monthly_grant_service import process_monthly_grants

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _build_paginated(
    items: list,
    total: int,
    limit: int,
    offset: int,
    item_cls,
) -> PaginatedItems:
    """Serialize ORM instances through their Pydantic model.

    UUID primary keys are converted to str here so that Pydantic's
    ``from_attributes`` validator receives plain strings.
    """
    serialized: list = []
    for it in items:
        d = {c.key: getattr(it, c.key) for c in it.__table__.columns}
        # Convert any UUID values to str for the pydantic model
        for k, v in d.items():
            if isinstance(v, uuid.UUID):
                d[k] = str(v)
        serialized.append(item_cls.model_validate(d))
    return PaginatedItems(
        items=serialized,
        total=total,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# POST /credits/grant (S04-T04 — existing)
# ---------------------------------------------------------------------------


@router.post(
    "/credits/grant",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def admin_grant_credits(
    admin: Annotated[User, Depends(PermissionChecker("credits:grant"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: AdminGrantRequest,
):
    """Admin grants credits to a specified user.

    Requires ``credits:grant`` permission (admin role, or operator with
    explicit grant — currently admin-only).
    """
    # Validate target user_id format
    try:
        target_user_id = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Invalid user_id: {body.user_id}",
            },
        )

    # Verify target user exists
    target_result = await db.execute(
        select(User).where(User.id == target_user_id)
    )
    target_user = target_result.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"Target user not found: {body.user_id}",
            },
        )

    # Grant credits
    try:
        new_balance = await grant_credits(
            db=db,
            user_id=target_user_id,
            amount=body.amount,
            source_type="manual",
            source_id=str(admin.id),
            description=body.description or f"Admin grant by {admin.account}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    return success_response(
        data=AdminGrantResponse(
            user_id=str(target_user_id),
            amount=body.amount,
            new_balance=new_balance,
            description=body.description,
        ).model_dump()
    )


# ---------------------------------------------------------------------------
# GET /users (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/users")
async def admin_list_users(
    admin: Annotated[User, Depends(PermissionChecker("users:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all users (requires ``users:read`` permission). Never returns password_hash."""
    items, total = await admin_service.list_users(db, limit=limit, offset=offset)
    data = _build_paginated(items, total, limit, offset, AdminUserItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /orders (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/orders")
async def admin_list_orders(
    admin: Annotated[User, Depends(PermissionChecker("orders:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all recharge orders (requires ``orders:read`` permission)."""
    items, total = await admin_service.list_orders(db, limit=limit, offset=offset)
    data = _build_paginated(items, total, limit, offset, AdminOrderItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /credit-accounts (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/credit-accounts")
async def admin_list_credit_accounts(
    admin: Annotated[User, Depends(PermissionChecker("users:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all credit accounts (requires ``users:read`` permission)."""
    items, total = await admin_service.list_credit_accounts(
        db, limit=limit, offset=offset
    )
    data = _build_paginated(items, total, limit, offset, AdminCreditAccountItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /provider-logs (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/provider-logs")
async def admin_list_provider_logs(
    admin: Annotated[User, Depends(PermissionChecker("provider_logs:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all provider call logs (requires ``provider_logs:read`` permission). Never returns raw payload."""
    items, total = await admin_service.list_provider_logs(
        db, limit=limit, offset=offset
    )
    data = _build_paginated(items, total, limit, offset, AdminProviderLogItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /usage-events (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/usage-events")
async def admin_list_usage_events(
    admin: Annotated[User, Depends(PermissionChecker("usage_events:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all usage events (requires ``usage_events:read`` permission). Never returns metadata_json."""
    items, total = await admin_service.list_usage_events(
        db, limit=limit, offset=offset
    )
    data = _build_paginated(items, total, limit, offset, AdminUsageEventItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# POST /monthly-grant/run (S05-R04 — new)
# ---------------------------------------------------------------------------


@router.post("/monthly-grant/run")
async def admin_run_monthly_grant(
    admin: Annotated[User, Depends(PermissionChecker("credits:grant"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: MonthlyGrantRequest = MonthlyGrantRequest(),
):
    """Manually trigger the monthly credit grant (requires ``credits:grant``).

    Defaults to the **current UTC year/month** when no target is specified.
    """
    now = datetime.now(timezone.utc)
    year = body.year or now.year
    month = body.month or now.month

    summary = await process_monthly_grants(db, year=year, month=month)
    return success_response(
        data=MonthlyGrantResponse(
            granted=summary.granted,
            skipped=summary.skipped,
            failed=summary.failed,
            errors=summary.errors,
        ).model_dump()
    )


# ---------------------------------------------------------------------------
# GET /provider-health (S05-R05 — new)
# ---------------------------------------------------------------------------


@router.get("/provider-health")
async def admin_provider_health(
    admin: Annotated[User, Depends(PermissionChecker("provider_logs:read"))],
):
    """Return circuit breaker status for all registered providers.

    Requires ``provider_logs:read`` permission (admin or operator).
    """
    cb_registry = get_circuit_breaker_registry()
    status_all = cb_registry.status_all()
    providers = {
        name: ProviderHealthItem(**status)
        for name, status in status_all.items()
    }
    return success_response(
        data=ProviderHealthResponse(providers=providers).model_dump()
    )
