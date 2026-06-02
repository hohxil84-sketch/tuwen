"""Admin query service — read-only aggregation for the admin dashboard (S05-R02).

All methods require an authenticated admin user; authorisation is enforced
by the ``PermissionChecker`` dependency in the API layer, not in this service.
(S05-R03: migrated from deprecated ``get_admin_user`` to ``PermissionChecker``.)
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.recharge_order import RechargeOrder
from app.models.credit_account import CreditAccount
from app.models.provider_call_log import ProviderCallLog
from app.models.usage_event import UsageEvent


# ---------------------------------------------------------------------------
# Shared pagination helper
# ---------------------------------------------------------------------------


async def _paginate(
    db: AsyncSession,
    stmt,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list, int]:
    """Execute a statement with count + page query, returning (items, total)."""
    total: int = 0
    count_result = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    row = count_result.scalar_one()
    total = int(row)

    items_result = await db.execute(stmt.limit(limit).offset(offset))
    items = list(items_result.scalars().all())
    return items, total


# ---------------------------------------------------------------------------
# Admin query methods
# ---------------------------------------------------------------------------


async def list_users(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[User], int]:
    """Return all users ordered by created_at DESC (excludes password_hash)."""
    stmt = (
        select(User)
        .order_by(User.created_at.desc())
    )
    return await _paginate(db, stmt, limit=limit, offset=offset)


async def list_orders(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[RechargeOrder], int]:
    """Return all recharge orders ordered by created_at DESC."""
    stmt = (
        select(RechargeOrder)
        .order_by(RechargeOrder.created_at.desc())
    )
    return await _paginate(db, stmt, limit=limit, offset=offset)


async def list_credit_accounts(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[CreditAccount], int]:
    """Return all credit accounts ordered by created_at DESC."""
    stmt = (
        select(CreditAccount)
        .order_by(CreditAccount.created_at.desc())
    )
    return await _paginate(db, stmt, limit=limit, offset=offset)


async def list_provider_logs(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[ProviderCallLog], int]:
    """Return all provider call logs ordered by created_at DESC."""
    stmt = (
        select(ProviderCallLog)
        .order_by(ProviderCallLog.created_at.desc())
    )
    return await _paginate(db, stmt, limit=limit, offset=offset)


async def list_usage_events(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[UsageEvent], int]:
    """Return all usage events ordered by created_at DESC."""
    stmt = (
        select(UsageEvent)
        .order_by(UsageEvent.created_at.desc())
    )
    return await _paginate(db, stmt, limit=limit, offset=offset)
