"""Monthly credit grant service — 月度积分发放调度器 (S05-R04).

Processes monthly credit grants for all eligible users based on their plan's
``monthly_credits`` configuration.  Idempotent: each (user, year, month)
combination is granted at most once.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.plan import Plan
from app.models.user import User
from app.services.credit_service import grant_credits

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# source_type used for monthly grant ledger entries.  Must be one of
# credit_service._VALID_SOURCE_TYPES — "system" is the allowed value.
GRANT_SOURCE_TYPE = "system"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GrantSummary:
    """Result summary returned by ``process_monthly_grants``."""

    granted: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Idempotency helpers
# ---------------------------------------------------------------------------


def _make_source_id(user_id: uuid.UUID, year: int, month: int) -> str:
    """Canonical idempotency key for a monthly grant."""
    return f"{user_id}:{year}-{month:02d}"


async def _already_granted(
    db: AsyncSession,
    user_id: uuid.UUID,
    source_id: str,
) -> bool:
    """Return True if a ledger entry already exists for this idempotency key."""
    result = await db.execute(
        select(CreditLedger.id).where(
            and_(
                CreditLedger.user_id == user_id,
                CreditLedger.source_type == GRANT_SOURCE_TYPE,
                CreditLedger.source_id == source_id,
            )
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Single-user grant
# ---------------------------------------------------------------------------


async def grant_monthly_credits_for_user(
    db: AsyncSession,
    user: User,
    plan: Plan,
    year: int,
    month: int,
    *,
    dry_run: bool = False,
) -> tuple[bool, str | None]:
    """Grant monthly credits to a single user.

    Args:
        db: Active database session.
        user: The user to grant credits to.
        plan: The user's plan (must have ``monthly_credits > 0``).
        year: Target year.
        month: Target month (1-12).
        dry_run: If True, only check whether the grant *would* happen.

    Returns:
        (granted: bool, error_message: str | None)
        - ``(True, None)`` — grant succeeded or would succeed (dry_run)
        - ``(False, None)`` — skipped (already granted this month)
        - ``(False, "error text")`` — failed
    """
    source_id = _make_source_id(user.id, year, month)

    # Idempotency check
    if await _already_granted(db, user.id, source_id):
        return False, None  # skipped

    if dry_run:
        return True, None

    try:
        await grant_credits(
            db=db,
            user_id=user.id,
            amount=plan.monthly_credits,
            source_type=GRANT_SOURCE_TYPE,
            source_id=source_id,
            description=f"Monthly grant {year}-{month:02d}: {plan.monthly_credits} credits",
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Batch orchestrator
# ---------------------------------------------------------------------------


async def process_monthly_grants(
    db: AsyncSession,
    year: int,
    month: int,
    *,
    dry_run: bool = False,
) -> GrantSummary:
    """Process monthly credit grants for all eligible active users.

    Eligibility:
    - ``users.status == "active"``
    - ``credit_accounts.status == "active"``
    - ``plans.monthly_credits > 0``
    - Not already granted for this (year, month)

    Args:
        db: Active database session.
        year: Target year (e.g. 2026).
        month: Target month (1-12).
        dry_run: If True, only count who *would* be granted — no writes.

    Returns:
        ``GrantSummary`` with counts.
    """
    summary = GrantSummary()

    # Query eligible users: active user + active credit account + plan with monthly_credits > 0
    stmt = (
        select(User, Plan)
        .join(CreditAccount, CreditAccount.user_id == User.id)
        .join(Plan, Plan.code == CreditAccount.plan_code)
        .where(
            and_(
                User.status == "active",
                CreditAccount.status == "active",
                Plan.monthly_credits > 0,
            )
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    for user, plan in rows:
        granted, error = await grant_monthly_credits_for_user(
            db, user, plan, year, month, dry_run=dry_run,
        )
        if error:
            summary.failed += 1
            summary.errors.append({
                "user_id": str(user.id),
                "account": user.account,
                "plan_code": plan.code,
                "monthly_credits": plan.monthly_credits,
                "error": error,
            })
        elif granted:
            summary.granted += 1
        else:
            summary.skipped += 1

    return summary
