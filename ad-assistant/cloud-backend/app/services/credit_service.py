"""Credit service — 用户 AI 算力账户与流水基础操作.

本模块只提供余额查询、账户创建和流水查询。不实现真实扣费、充值、支付或套餐发放。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
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
