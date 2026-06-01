"""Plan service — 套餐查询."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan


async def list_active_plans(
    *,
    db: AsyncSession,
) -> list[Plan]:
    """Return all active plans ordered by sort_order ascending."""
    result = await db.execute(
        select(Plan)
        .where(Plan.status == "active")
        .order_by(Plan.sort_order.asc())
    )
    return list(result.scalars().all())


async def get_plan_by_code(
    *,
    db: AsyncSession,
    code: str,
) -> Plan | None:
    """Return a single plan by its code, or None."""
    result = await db.execute(
        select(Plan).where(Plan.code == code, Plan.status == "active")
    )
    return result.scalar_one_or_none()
