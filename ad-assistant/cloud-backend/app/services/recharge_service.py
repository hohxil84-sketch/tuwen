"""Recharge service — 用户充值/购买套餐 with risk control.

All operations (order, plan update, credit grant, ledger) happen inside the
caller's transaction.  The caller (API route) owns the ``db`` session and
commit/rollback boundary.

S05-R06 adds:
- Order status machine (PENDING → COMPLETED | FAILED)
- Idempotency key (duplicate detection)
- Amount validation (min/max)
- Rate limiting (sliding window)
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.credit_account import CreditAccount
from app.models.plan import Plan
from app.models.recharge_order import (
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_PENDING,
    RechargeOrder,
)
from app.models.user import User
from app.services.credit_service import grant_credits
from app.services.plan_service import get_plan_by_code

# ---------------------------------------------------------------------------
# Custom exceptions — caught by API layer and mapped to HTTP status codes
# ---------------------------------------------------------------------------


class RechargeRiskError(ValueError):
    """Base for all recharge risk-control rejections."""


class DuplicateOrderError(RechargeRiskError):
    """Idempotency key collision — the same order was already submitted."""


class RateLimitExceededError(RechargeRiskError):
    """Too many recharge requests in the rate-limit window."""


class InvalidRechargeAmountError(RechargeRiskError):
    """Amount is out of the allowed min/max range."""


class InvalidStatusTransitionError(RechargeRiskError):
    """Attempted a forbidden order status transition."""


# ---------------------------------------------------------------------------
# Order status guards
# ---------------------------------------------------------------------------


def _validate_transition(from_status: str, to_status: str) -> None:
    """Raise InvalidStatusTransitionError if *from_status → to_status* is
    not in the allowed transition table."""
    from app.models.recharge_order import _ALLOWED_TRANSITIONS

    allowed = _ALLOWED_TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot transition order from '{from_status}' to '{to_status}'"
        )


async def _complete_order(*, db: AsyncSession, order: RechargeOrder) -> None:
    """Transition *order* to COMPLETED (state-guarded)."""
    _validate_transition(order.status, ORDER_STATUS_COMPLETED)
    order.status = ORDER_STATUS_COMPLETED
    order.completed_at = datetime.now(timezone.utc)
    db.add(order)


async def _fail_order(*, db: AsyncSession, order: RechargeOrder) -> None:
    """Transition *order* to FAILED (state-guarded)."""
    _validate_transition(order.status, ORDER_STATUS_FAILED)
    order.status = ORDER_STATUS_FAILED
    order.failed_at = datetime.now(timezone.utc)
    db.add(order)


# ---------------------------------------------------------------------------
# Risk control validators
# ---------------------------------------------------------------------------


def _validate_amount(*, amount_cny: int) -> None:
    """Validate recharge amount against configured min/max.

    Raises:
        InvalidRechargeAmountError: If amount is outside [min, max] range.
    """
    if amount_cny < settings.MIN_RECHARGE_AMOUNT_CNY:
        raise InvalidRechargeAmountError(
            f"amount_cny must be >= {settings.MIN_RECHARGE_AMOUNT_CNY}, got {amount_cny}"
        )
    if amount_cny > settings.MAX_RECHARGE_AMOUNT_CNY:
        raise InvalidRechargeAmountError(
            f"amount_cny must be <= {settings.MAX_RECHARGE_AMOUNT_CNY}, got {amount_cny}"
        )


async def _check_rate_limit(
    *, db: AsyncSession, user_id: uuid.UUID
) -> None:
    """Check whether *user_id* has exceeded the recharge rate limit.

    Uses a sliding window: counts orders whose ``created_at`` falls within
    the last ``RECHARGE_RATE_LIMIT_WINDOW_SECONDS`` seconds.

    Raises:
        RateLimitExceededError: If the count equals or exceeds the threshold.
    """
    window_start = datetime.now(timezone.utc) - timedelta(
        seconds=settings.RECHARGE_RATE_LIMIT_WINDOW_SECONDS
    )
    count_q = (
        select(func.count())
        .select_from(RechargeOrder)
        .where(
            RechargeOrder.user_id == user_id,
            RechargeOrder.created_at >= window_start,
        )
    )
    recent_count: int = (await db.execute(count_q)).scalar() or 0

    if recent_count >= settings.RECHARGE_RATE_LIMIT_COUNT:
        raise RateLimitExceededError(
            f"Rate limit exceeded: max {settings.RECHARGE_RATE_LIMIT_COUNT} "
            f"recharges per {settings.RECHARGE_RATE_LIMIT_WINDOW_SECONDS}s "
            f"(current: {recent_count})"
        )


async def _resolve_idempotency(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    idempotency_key: str | None,
) -> RechargeOrder | None:
    """Check for an existing order with the same idempotency_key.

    Returns:
        The existing ``RechargeOrder`` if found (COMPLETED → replay),
        or ``None`` if no existing order or the existing order is FAILED
        (allows retry).

    Raises:
        DuplicateOrderError: If a PENDING order with the same key exists.
    """
    if idempotency_key is None:
        return None

    result = await db.execute(
        select(RechargeOrder).where(
            RechargeOrder.user_id == user_id,
            RechargeOrder.idempotency_key == idempotency_key,
        )
    )
    existing: RechargeOrder | None = result.scalar_one_or_none()

    if existing is None:
        return None

    if existing.status == ORDER_STATUS_COMPLETED:
        # Idempotent replay — return the existing completed order.
        return existing

    if existing.status == ORDER_STATUS_PENDING:
        # PENDING → conflict (already being processed).
        raise DuplicateOrderError(
            f"An order with idempotency_key '{idempotency_key}' is already "
            f"being processed (status: pending). Please wait for it to complete."
        )

    # FAILED → allow retry with the same key (the partial unique index
    # also excludes FAILED rows, so a new order can be inserted).
    return None


# ---------------------------------------------------------------------------
# Core recharge orchestration
# ---------------------------------------------------------------------------


async def create_recharge_order(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_code: str | None = None,
    amount_cny: int | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create a recharge order with risk-control checks.

    **Order of checks** (fail-fast):
    1. Idempotency — reuse completed order, reject duplicate pending
    2. Amount validation — min/max range
    3. Rate limiting — sliding window count
    4. Plan resolution & order creation
    5. Simulated payment → complete order + grant credits

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
        idempotency_key: Optional client-generated idempotency key.

    Returns:
        dict with keys: ``order_id``, ``plan_code``, ``amount_cny``,
        ``credits``, ``new_balance``, ``status``, ``payment_method``,
        ``plan_changed``, ``idempotent_replay``.

    Raises:
        DuplicateOrderError: Idempotency key collision with a pending order.
        InvalidRechargeAmountError: Amount out of min/max range.
        RateLimitExceededError: Too many requests in the rate window.
        ValueError: Plan not found, missing params, other validation errors.
    """
    # ── 1. Idempotency check ────────────────────────────────────────────
    existing = await _resolve_idempotency(
        db=db, user_id=user_id, idempotency_key=idempotency_key,
    )
    if existing is not None:
        # Idempotent replay — return the existing completed order data.
        from app.services.credit_service import get_or_create_credit_account

        account = await get_or_create_credit_account(db=db, user_id=user_id)
        return {
            "order_id": str(existing.id),
            "plan_code": existing.plan_code,
            "amount_cny": existing.amount_cny,
            "credits": existing.credits,
            "new_balance": account.balance,
            "status": existing.status,
            "payment_method": existing.payment_method,
            "plan_changed": False,
            "idempotent_replay": True,
        }

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
        _amount_cny = amount_cny
        _credits = amount_cny * settings.CREDITS_PER_CNY
        _plan_code = None
    else:
        raise ValueError("Either plan_code or amount_cny must be provided")

    # ── 2. Amount validation ────────────────────────────────────────────
    _validate_amount(amount_cny=_amount_cny)

    # ── 3. Rate limiting ────────────────────────────────────────────────
    await _check_rate_limit(db=db, user_id=user_id)

    # ── Determine payment method and status ─────────────────────────────
    simulated_enabled = settings.ENABLE_SIMULATED_PAYMENT
    payment_method = "simulated"

    # ── 4. Create the recharge order ────────────────────────────────────
    now = datetime.now(timezone.utc)
    order = RechargeOrder(
        user_id=user_id,
        plan_code=_plan_code,
        amount_cny=_amount_cny,
        credits=_credits,
        payment_method=payment_method,
        status=ORDER_STATUS_PENDING,  # always start pending
        idempotency_key=idempotency_key,
        description=(
            f"Recharge: {_plan_code or 'custom'} — "
            f"{_amount_cny} CNY → {_credits} credits"
        ),
        created_at=now,
    )
    db.add(order)
    await db.flush()

    # ── 5. Simulated payment → complete + grant ─────────────────────────
    plan_changed = False
    new_balance: int = 0
    idempotent_replay = False

    if simulated_enabled:
        try:
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
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
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

            await _complete_order(db=db, order=order)
            await db.flush()

        except Exception:
            # If credit grant or plan update fails, mark order as FAILED
            # and re-raise so the caller can rollback.
            await _fail_order(db=db, order=order)
            await db.flush()
            raise

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
        "idempotent_replay": idempotent_replay,
    }
