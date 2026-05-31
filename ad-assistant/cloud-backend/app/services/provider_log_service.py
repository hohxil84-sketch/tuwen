"""Provider call log service — record and query AI Provider calls."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider_call_log import ProviderCallLog

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

_VALID_STATUSES = {"success", "error"}


def _validate_provider_call(
    *,
    status: str,
    error_code: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    estimated_cost: float | None,
    credits_charged: int | None,
    latency_ms: int | None,
) -> None:
    """校验 provider_call_log 写入参数的合法性。

    规则：
    1. status 必须是 ``"success"`` 或 ``"error"``。
    2. status=error 时 error_code 必须非空。
    3. status=success 时 error_code 必须为空。
    4. token 类字段（prompt/completion/total_tokens）必须非负。
    5. estimated_cost 必须非负。
    6. credits_charged 必须非负。
    7. latency_ms 必须非负。
    """
    # 规则 1
    if status not in _VALID_STATUSES:
        raise ValueError("INVALID_STATUS")

    # 规则 2
    if status == "error" and not error_code:
        raise ValueError("ERROR_CODE_REQUIRED")

    # 规则 3
    if status == "success" and error_code:
        raise ValueError("ERROR_CODE_NOT_ALLOWED_FOR_SUCCESS")

    # 规则 4
    if prompt_tokens < 0:
        raise ValueError("PROMPT_TOKENS_NEGATIVE")
    if completion_tokens < 0:
        raise ValueError("COMPLETION_TOKENS_NEGATIVE")
    if total_tokens < 0:
        raise ValueError("TOTAL_TOKENS_NEGATIVE")

    # 规则 5
    if estimated_cost is not None and estimated_cost < 0:
        raise ValueError("ESTIMATED_COST_NEGATIVE")

    # 规则 6
    if credits_charged is not None and credits_charged < 0:
        raise ValueError("CREDITS_CHARGED_NEGATIVE")

    # 规则 7
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("LATENCY_MS_NEGATIVE")


# ---------------------------------------------------------------------------
# 写入
# ---------------------------------------------------------------------------


async def record_provider_call(
    *,
    db: AsyncSession,
    provider: str,
    model: str,
    feature: str,
    status: str,
    user_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    request_id: str | None = None,
    error_code: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    estimated_cost: float | None = None,
    credits_charged: int | None = None,
    latency_ms: int | None = None,
) -> dict:
    """记录一次 AI Provider 调用（成功或失败均可记录）。

    不记录 prompt 原文、图片原文、API Key、用户隐私内容。
    estimated_cost 只能由后端计算，不能来自前端。

    写入前会进行参数校验，不合法参数抛出 ``ValueError("CODE")``。
    """
    _validate_provider_call(
        status=status,
        error_code=error_code,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        credits_charged=credits_charged,
        latency_ms=latency_ms,
    )

    entry = ProviderCallLog(
        request_id=request_id,
        user_id=user_id,
        device_id=device_id,
        provider=provider,
        model=model,
        feature=feature,
        status=status,
        error_code=error_code if status == "error" else None,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        credits_charged=credits_charged,
        latency_ms=latency_ms,
    )
    db.add(entry)
    await db.flush()

    return {
        "id": str(entry.id),
        "provider": entry.provider,
        "model": entry.model,
        "feature": entry.feature,
        "status": entry.status,
        "total_tokens": entry.total_tokens,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------


async def list_provider_call_logs(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    feature: str | None = None,
    status: str | None = None,
) -> dict:
    """查询当前用户的 Provider 调用日志列表（按时间倒序，支持分页和筛选）."""
    # 计数
    count_query = select(func.count()).select_from(ProviderCallLog).where(
        ProviderCallLog.user_id == user_id
    )
    if feature:
        count_query = count_query.where(ProviderCallLog.feature == feature)
    if status:
        count_query = count_query.where(ProviderCallLog.status == status)
    total = (await db.execute(count_query)).scalar() or 0

    # 查询列表
    query = (
        select(ProviderCallLog)
        .where(ProviderCallLog.user_id == user_id)
        .order_by(ProviderCallLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if feature:
        query = query.where(ProviderCallLog.feature == feature)
    if status:
        query = query.where(ProviderCallLog.status == status)

    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "request_id": r.request_id,
                "user_id": str(r.user_id) if r.user_id else None,
                "device_id": str(r.device_id) if r.device_id else None,
                "provider": r.provider,
                "model": r.model,
                "feature": r.feature,
                "status": r.status,
                "error_code": r.error_code,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "estimated_cost": float(r.estimated_cost) if r.estimated_cost else None,
                "credits_charged": r.credits_charged,
                "latency_ms": r.latency_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
