"""Recharge service — 用户充值/购买套餐."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.plan import Plan
from app.models.recharge_order import RechargeOrder
from app.services.credit_service import grant_credits
from app.services.plan_service import get_plan_by_code


async def create_recharge_order(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_code: str | None = None,
    amount_cny: int | None = None,
) -> dict:
    """Create a recharge order and grant credits to the user.

    If *plan_code* is provided, the plan's price and monthly credits are used.
    Otherwise *amount_cny* must be provided as a custom top-up amount.

    Credits are computed as ``amount_cny * CREDITS_PER_CNY``.
    Payment is simulated — the order is created as ``completed`` immediately.

    Args:
        db: Active database session.
        user_id: User making the recharge.
        plan_code: Optional plan code to purchase.
        amount_cny: Custom recharge amount in CNY (used when plan_code is None).

    Returns:
        dict with keys: ``order_id``, ``plan_code``, ``amount_cny``,
        ``credits``, ``new_balance``, ``status``.

    Raises:
        ValueError: If plan_code not found, amount invalid, or missing both params.
    """
    # Resolve amount and credits
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

    # Create the recharge order
    order = RechargeOrder(
        user_id=user_id,
        plan_code=_plan_code,
        amount_cny=_amount_cny,
        credits=_credits,
        payment_method="simulated",
        status="completed",
        description=f"Recharge: {_plan_code or 'custom'} — {_amount_cny} CNY → {_credits} credits",
    )
    db.add(order)
    await db.flush()

    # Grant credits atomically
    new_balance = await grant_credits(
        db=db,
        user_id=user_id,
        amount=_credits,
        source_type="order",
        source_id=str(order.id),
        description=order.description,
    )

    return {
        "order_id": str(order.id),
        "plan_code": _plan_code,
        "amount_cny": _amount_cny,
        "credits": _credits,
        "new_balance": new_balance,
        "status": order.status,
    }
