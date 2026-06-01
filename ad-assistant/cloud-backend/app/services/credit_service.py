"""Credit service — 用户 AI 算力账户与流水基础操作.

本模块提供余额查询、账户创建、流水查询、扣费操作、积分授予。
不实现真实支付或套餐发放（见 recharge_service）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger

# ---------------------------------------------------------------------------
# 合法枚举值
# ---------------------------------------------------------------------------

_VALID_CHANGE_TYPES = frozenset({"grant", "consume", "refund", "adjust"})
_VALID_SOURCE_TYPES = frozenset({"system", "provider_call", "manual", "order"})


# ---------------------------------------------------------------------------
# 账户
# ---------------------------------------------------------------------------


async def get_or_create_credit_account(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_code: str = "standard",
) -> CreditAccount:
    """获取或创建用户 AI 算力账户。

    若账户不存在，创建余额为 0 的基础账户。不自动发放套餐额度。
    不读取客户端传入的余额。
    """
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.user_id == user_id)
    )
    account: CreditAccount | None = result.scalar_one_or_none()

    if account is not None:
        return account

    account = CreditAccount(
        user_id=user_id,
        plan_code=plan_code,
        monthly_grant=0,
        balance=0,
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def get_credit_balance(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """返回当前用户余额信息。

    若账户不存在，先创建基础账户再返回。
    """
    account = await get_or_create_credit_account(db=db, user_id=user_id)
    return {
        "user_id": str(account.user_id),
        "plan_code": account.plan_code,
        "monthly_grant": account.monthly_grant,
        "balance": account.balance,
        "period_start": account.period_start.isoformat() if account.period_start else None,
        "period_end": account.period_end.isoformat() if account.period_end else None,
        "status": account.status,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }


# ---------------------------------------------------------------------------
# 流水
# ---------------------------------------------------------------------------


async def list_credit_ledger(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """查询当前用户自己的流水（按时间倒序，支持分页）。"""
    # 计数
    count_query = (
        select(func.count())
        .select_from(CreditLedger)
        .where(CreditLedger.user_id == user_id)
    )
    total = (await db.execute(count_query)).scalar() or 0

    # 查询列表
    query = (
        select(CreditLedger)
        .where(CreditLedger.user_id == user_id)
        .order_by(CreditLedger.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "change_type": r.change_type,
                "amount": r.amount,
                "balance_after": r.balance_after,
                "source_type": r.source_type,
                "source_id": r.source_id,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# 内部写流水（仅供测试和后续服务复用，不暴露为公共 API）
# ---------------------------------------------------------------------------


async def record_credit_ledger(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID | None,
    change_type: str,
    amount: int,
    balance_after: int,
    source_type: str,
    source_id: str | None = None,
    description: str | None = None,
) -> CreditLedger:
    """记录一条 AI 算力流水（内部函数，测试和后续服务复用）。

    校验规则：
    - change_type 必须在合法枚举内
    - source_type 必须在合法枚举内
    - amount 不能为 0
    - balance_after 不能为负
    - consume 类型必须 amount < 0

    Raises:
        ValueError: 参数校验不通过。
    """
    # 校验 change_type
    if change_type not in _VALID_CHANGE_TYPES:
        raise ValueError(
            f"Invalid change_type '{change_type}', must be one of {sorted(_VALID_CHANGE_TYPES)}"
        )

    # 校验 source_type
    if source_type not in _VALID_SOURCE_TYPES:
        raise ValueError(
            f"Invalid source_type '{source_type}', must be one of {sorted(_VALID_SOURCE_TYPES)}"
        )

    # 校验 amount 非零
    if amount == 0:
        raise ValueError("amount must not be 0")

    # 校验 balance_after 非负
    if balance_after < 0:
        raise ValueError(f"balance_after must be >= 0, got {balance_after}")

    # 校验 consume 类型必须 amount < 0
    if change_type == "consume" and amount >= 0:
        raise ValueError(f"consume amount must be negative, got {amount}")

    ledger = CreditLedger(
        user_id=user_id,
        account_id=account_id,
        change_type=change_type,
        amount=amount,
        balance_after=balance_after,
        source_type=source_type,
        source_id=source_id,
        description=description,
    )
    db.add(ledger)
    await db.flush()
    return ledger


# ---------------------------------------------------------------------------
# Sprint-03 Task-03: real credit deduction
# ---------------------------------------------------------------------------


async def deduct_credits(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    source_id: str | None = None,
    description: str | None = None,
) -> int:
    """Atomically deduct credits from the user's balance.

    Reads the current balance, deducts up to ``amount`` (partial deduction
    if insufficient), writes a ``consume`` entry to ``credit_ledger``, and
    returns the number of credits actually deducted.

    All operations happen within the caller's transaction (``db`` session).

    Args:
        db: Active database session.
        user_id: User whose balance will be deducted.
        amount: Maximum credits to deduct (must be >= 0).
        source_id: Optional identifier (e.g. request_id) for the ledger entry.
        description: Optional human-readable description.

    Returns:
        int: The number of credits actually deducted (0 if amount <= 0
        or balance is 0).

    Raises:
        ValueError: If ``amount`` is negative.
    """
    if amount < 0:
        raise ValueError(f"amount must be >= 0, got {amount}")
    if amount == 0:
        return 0

    # Get or create the credit account
    account = await get_or_create_credit_account(db=db, user_id=user_id)

    # Determine actual deduction (partial if balance insufficient)
    actual_deduct = min(amount, account.balance)
    if actual_deduct <= 0:
        return 0

    new_balance = account.balance - actual_deduct

    # Atomic update: SET balance = balance - actual_deduct
    await db.execute(
        update(CreditAccount)
        .where(CreditAccount.id == account.id)
        .values(balance=new_balance)
    )
    # Update the in-memory object to stay consistent
    account.balance = new_balance

    # Write the ledger entry
    await record_credit_ledger(
        db=db,
        user_id=user_id,
        account_id=account.id,
        change_type="consume",
        amount=-actual_deduct,
        balance_after=new_balance,
        source_type="provider_call",
        source_id=source_id,
        description=description or f"Provider call deduction: {actual_deduct} credits",
    )

    return actual_deduct


# ---------------------------------------------------------------------------
# Sprint-04 Task-04: credit grant (充值 / 赠送 / 月度发放)
# ---------------------------------------------------------------------------


async def grant_credits(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    source_type: str = "system",
    source_id: str | None = None,
    description: str | None = None,
) -> int:
    """Atomically grant credits to a user's balance.

    Reads the current balance, adds *amount*, writes a ``grant`` entry to
    ``credit_ledger``, and returns the **new balance** after the grant.

    All operations happen within the caller's transaction (``db`` session).

    Args:
        db: Active database session.
        user_id: User receiving the credits.
        amount: Credits to grant (must be > 0).
        source_type: Ledger source type — ``"system"`` (monthly grant),
                     ``"order"`` (recharge), or ``"manual"`` (admin).
        source_id: Optional identifier (e.g. order_id) for the ledger entry.
        description: Optional human-readable description.

    Returns:
        int: The new balance after granting credits.

    Raises:
        ValueError: If ``amount`` is not positive.
    """
    if amount <= 0:
        raise ValueError(f"amount must be > 0, got {amount}")

    # Get or create the credit account
    account = await get_or_create_credit_account(db=db, user_id=user_id)

    new_balance = account.balance + amount

    # Atomic update: SET balance = balance + amount
    await db.execute(
        update(CreditAccount)
        .where(CreditAccount.id == account.id)
        .values(balance=new_balance)
    )
    # Update the in-memory object to stay consistent
    account.balance = new_balance

    # Write the ledger entry
    await record_credit_ledger(
        db=db,
        user_id=user_id,
        account_id=account.id,
        change_type="grant",
        amount=amount,
        balance_after=new_balance,
        source_type=source_type,
        source_id=source_id,
        description=description or f"Grant: {amount} credits",
    )

    return new_balance
