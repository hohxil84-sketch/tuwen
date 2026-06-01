"""Dashboard aggregation service — Sprint-04 Task-02.

Aggregates credit balance, usage counts, and recent activity for the dashboard
summary endpoint. All queries are scoped to the authenticated user.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_account import CreditAccount
from app.models.provider_call_log import ProviderCallLog
from app.models.user import User


async def get_dashboard_summary(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """Aggregate dashboard data for a single user.

    Returns a dict with keys matching ``DashboardSummaryData``:
    - credit_balance
    - today_calls
    - monthly_calls
    - plan_code
    - recent_activity

    When the user has no ``CreditAccount`` yet, ``credit_balance`` defaults to 0
    and ``plan_code`` is read from the ``User`` record.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ------------------------------------------------------------------
    # Credit account (balance + plan_code)
    # ------------------------------------------------------------------
    credit_result = await db.execute(
        select(CreditAccount).where(CreditAccount.user_id == user_id)
    )
    credit_account: CreditAccount | None = credit_result.scalar_one_or_none()

    if credit_account is not None:
        credit_balance = credit_account.balance
        plan_code = credit_account.plan_code
    else:
        credit_balance = 0
        # Fall back to user.plan_code
        user_result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = user_result.scalar_one_or_none()
        plan_code = user.plan_code if user is not None else "standard"

    # ------------------------------------------------------------------
    # Today's successful calls
    # ------------------------------------------------------------------
    today_calls_result = await db.execute(
        select(func.count())
        .select_from(ProviderCallLog)
        .where(
            ProviderCallLog.user_id == user_id,
            ProviderCallLog.status == "success",
            ProviderCallLog.created_at >= today_start,
        )
    )
    today_calls: int = today_calls_result.scalar() or 0

    # ------------------------------------------------------------------
    # This month's successful calls
    # ------------------------------------------------------------------
    monthly_calls_result = await db.execute(
        select(func.count())
        .select_from(ProviderCallLog)
        .where(
            ProviderCallLog.user_id == user_id,
            ProviderCallLog.status == "success",
            ProviderCallLog.created_at >= month_start,
        )
    )
    monthly_calls: int = monthly_calls_result.scalar() or 0

    # ------------------------------------------------------------------
    # Recent activity (last 5 provider call logs, any status)
    # ------------------------------------------------------------------
    recent_result = await db.execute(
        select(ProviderCallLog)
        .where(ProviderCallLog.user_id == user_id)
        .order_by(ProviderCallLog.created_at.desc())
        .limit(5)
    )
    recent_rows = recent_result.scalars().all()

    recent_activity: list[dict] = []
    for row in recent_rows:
        recent_activity.append({
            "feature": row.feature,
            "provider": row.provider,
            "model": row.model,
            "status": row.status,
            "credits_charged": row.credits_charged or 0,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        })

    return {
        "credit_balance": credit_balance,
        "today_calls": today_calls,
        "monthly_calls": monthly_calls,
        "plan_code": plan_code,
        "recent_activity": recent_activity,
    }
