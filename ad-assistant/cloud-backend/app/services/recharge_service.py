"""Recharge service — 用户充值/购买套餐.

All operations (order, plan update, credit grant, ledger) happen inside the
caller's transaction.  The caller (API route) owns the ``db`` session and
commit/rollback boundary.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.credit_account import CreditAccount
from app.models.plan import Plan
from app.models.recharge_order import RechargeOrder
from app.models.user import User
from app.services.credit_service import grant_credits
from app.services.plan_service import get_plan_by_code


async def create_recharge_order(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_code: str | None = None,
    amount_cny: int | None = None,
) -> dict:
    """Create a recharge order and optionally grant credits.

    **Simulated payment gate** — controlled by ``ENABLE_SIMULATED_PAYMENT``:

    * ``False`` (default / production): creates a **pending** order, does
      **not** grant credits.  The order awaits a real payment callback.
    * ``True`` (dev / test): creates a **completed** order and grants
      credits immediately in the same transaction.

    **Plan purchase** — when *plan_code* is provided and different from the
    user's current plan, both ``users.plan_code`` and
    ``credit_accounts.plan_code`` are updated atomically.

    Args:
        db: Active database session (caller owns transaction).
        user_id: User making the recharge.
        plan_code: Optional plan code to purchase.
        amount_cny: Custom recharge amount in CNY (used when plan_code is None).

    Returns:
        dict with keys: ``order_id``, ``plan_code``, ``amount_cny``,
        ``credits``, ``new_balance``, ``status``, ``payment_method``,
        ``plan_changed``.

    Raises:
        ValueError: If plan_code not found, amount invalid, or missing both params.
    """
    # ── Resolve amount and credits ──────────────────────────────────────
    plan: Plan | None = None
    if plan_code is not None:
        plan = await get_plan_by_code(db=db, code=plan_code)
        if plan is None:
            raise ValueError(f"Plan '{plan_code}' not found or inactive")
        _amount_cny = plan.price_cny
        _credits = plan.monthly_credits
        _plan_code = plan.code
    elif amount_cny is not None:
        if amount_cny <= 0:
            raise ValueError(f"amount_cny must be > 0, got {amount_cny}")
        _amount_cny = amount_cny
        _credits = amount_cny * settings.CREDITS_PER_CNY
        _plan_code = None
    else:
        raise ValueError("Either plan_code or amount_cny must be provided")

    # ── Determine payment method and status ─────────────────────────────
    simulated_enabled = settings.ENABLE_SIMULATED_PAYMENT
    payment_method = "simulated"
    order_status = "completed" if simulated_enabled else "pending"

    # ── Create the recharge order ───────────────────────────────────────
    now = datetime.now(timezone.utc)
    order = RechargeOrder(
        user_id=user_id,
        plan_code=_plan_code,
        amount_cny=_amount_cny,
        credits=_credits,
        payment_method=payment_method,
        status=order_status,
        description=(
            f"Recharge: {_plan_code or 'custom'} — "
            f"{_amount_cny} CNY → {_credits} credits"
        ),
        created_at=now,
        completed_at=now if order_status == "completed" else None,
    )
    db.add(order)
    await db.flush()

    # ── Grant credits + plan upgrade (only when simulated payment is on) ─
    plan_changed = False
    new_balance: int = 0
    if simulated_enabled:
        # Grant credits atomically
        new_balance = await grant_credits(
            db=db,
            user_id=user_id,
            amount=_credits,
            source_type="order",
            source_id=str(order.id),
            description=order.description,
        )

        # Plan upgrade: only when payment is completed
        if plan is not None:
            from sqlalchemy import select as _select

            user_result = await db.execute(
                _select(User).where(User.id == user_id)
            )
            user_row = user_result.scalar_one_or_none()
            if user_row is not None and user_row.plan_code != plan.code:
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(plan_code=plan.code)
                )
                await db.execute(
                    update(CreditAccount)
                    .where(CreditAccount.user_id == user_id)
                    .values(plan_code=plan.code)
                )
                plan_changed = True
    else:
        # Return current balance without granting credits or changing plan
        from app.services.credit_service import get_or_create_credit_account

        account = await get_or_create_credit_account(db=db, user_id=user_id)
        new_balance = account.balance

    return {
        "order_id": str(order.id),
        "plan_code": _plan_code,
        "amount_cny": _amount_cny,
        "credits": _credits,
        "new_balance": new_balance,
        "status": order.status,
        "payment_method": payment_method,
        "plan_changed": plan_changed,
    }
