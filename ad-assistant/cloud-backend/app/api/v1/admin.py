"""Admin API routes — 管理员操作（查询、赠送积分等）."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminGrantRequest,
    AdminGrantResponse,
    AdminCreditAccountItem,
    AdminOrderItem,
    AdminProviderLogItem,
    AdminUsageEventItem,
    AdminUserItem,
    PaginatedItems,
)
from app.schemas.common import success_response
from app.services import admin_service
from app.services.credit_service import grant_credits

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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: AdminGrantRequest,
):
    """Admin grants credits to a specified user.

    Requires admin authentication (user ID in ADMIN_USER_IDS config).
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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all users (admin only).  Never returns password_hash."""
    items, total = await admin_service.list_users(db, limit=limit, offset=offset)
    data = _build_paginated(items, total, limit, offset, AdminUserItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /orders (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/orders")
async def admin_list_orders(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all recharge orders (admin only)."""
    items, total = await admin_service.list_orders(db, limit=limit, offset=offset)
    data = _build_paginated(items, total, limit, offset, AdminOrderItem)
    return success_response(data=data.model_dump())


# ---------------------------------------------------------------------------
# GET /credit-accounts (S05-R02 — new)
# ---------------------------------------------------------------------------


@router.get("/credit-accounts")
async def admin_list_credit_accounts(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all credit accounts (admin only)."""
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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all provider call logs (admin only).  Never returns raw payload."""
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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List all usage events (admin only).  Never returns metadata_json."""
    items, total = await admin_service.list_usage_events(
        db, limit=limit, offset=offset
    )
    data = _build_paginated(items, total, limit, offset, AdminUsageEventItem)
    return success_response(data=data.model_dump())
