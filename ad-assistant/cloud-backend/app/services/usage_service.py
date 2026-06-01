"""Usage event service — record and query feature usage events."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_event import UsageEvent

# ---------------------------------------------------------------------------
# Metadata 安全白名单 — 只允许以下 key 写入 metadata_json
# ---------------------------------------------------------------------------

_METADATA_ALLOWLIST: set[str] = {
    "image_count",
    "file_count",
    "source",
    "duration_ms",
    "result_count",
    "format",
    "width",
    "height",
    "page_count",
    "language",
    "engine",
    "mode",
    "quality",
    "size_bytes",
}

# 敏感词模式 — key 或 value 命中任一模式即拦截
_SENSITIVE_PATTERNS: list[str] = [
    "token",
    "api_key",
    "apikey",
    "password",
    "secret",
    "credential",
    "private_key",
    "authorization",
    "bearer",
    "access_key",
    "secret_key",
    "passwd",
    "pwd",
    "auth",
]


def _sanitize_metadata(metadata: dict | None) -> dict | None:
    """递归清洗 metadata，仅保留白名单 key，并拦截敏感值。

    规则：
    1. key 不在白名单 → 丢弃。
    2. key 在白名单但 value 为 dict/list → 递归清洗。
    3. 字符串 value 包含敏感模式 → 替换为 ``"[REDACTED]"``。
    4. 空 dict 最终返回 None。
    """
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        return None

    cleaned: dict = {}
    for key, value in metadata.items():
        # 规则 1：key 不在白名单 → 丢弃
        if key not in _METADATA_ALLOWLIST:
            continue

        # 规则 2：递归清洗嵌套结构
        if isinstance(value, dict):
            value = _sanitize_metadata(value)
            if value is None:
                continue
        elif isinstance(value, list):
            value = _sanitize_list(value)
            if value is None:
                continue
        elif isinstance(value, str):
            # 规则 3：字符串 value 命中敏感模式 → 替换
            if _contains_sensitive_pattern(value):
                value = "[REDACTED]"

        cleaned[key] = value

    # 规则 4：空 dict → None
    return cleaned if cleaned else None


def _sanitize_list(items: list) -> list | None:
    """递归清洗列表中的每个元素."""
    result: list = []
    for item in items:
        if isinstance(item, dict):
            cleaned = _sanitize_metadata(item)
            if cleaned is not None:
                result.append(cleaned)
        elif isinstance(item, list):
            cleaned = _sanitize_list(item)
            if cleaned is not None:
                result.append(cleaned)
        elif isinstance(item, str):
            if _contains_sensitive_pattern(item):
                result.append("[REDACTED]")
            else:
                result.append(item)
        else:
            result.append(item)
    return result if result else None


def _contains_sensitive_pattern(value: str) -> bool:
    """检查字符串是否包含敏感模式（大小写不敏感）."""
    lower = value.lower()
    return any(pattern in lower for pattern in _SENSITIVE_PATTERNS)


# ---------------------------------------------------------------------------
# 写入
# ---------------------------------------------------------------------------


async def record_usage_event(
    *,
    db: AsyncSession,
    event_type: str,
    feature: str,
    user_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    request_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """记录一条功能使用事件。

    metadata 经过白名单 + 递归敏感信息拦截，确保不落盘敏感内容。
    """
    safe_metadata = _sanitize_metadata(metadata)

    event = UsageEvent(
        user_id=user_id,
        device_id=device_id,
        event_type=event_type,
        feature=feature,
        request_id=request_id,
        metadata_json=safe_metadata,
    )
    db.add(event)
    await db.flush()

    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "feature": event.feature,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------


async def list_usage_events(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    feature: str | None = None,
) -> dict:
    """查询当前用户的使用事件列表（按时间倒序，支持分页和按 feature 筛选）."""
    # 计数
    count_query = select(func.count()).select_from(UsageEvent).where(
        UsageEvent.user_id == user_id
    )
    if feature:
        count_query = count_query.where(UsageEvent.feature == feature)
    total = (await db.execute(count_query)).scalar() or 0

    # 查询列表
    query = (
        select(UsageEvent)
        .where(UsageEvent.user_id == user_id)
        .order_by(UsageEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if feature:
        query = query.where(UsageEvent.feature == feature)

    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id) if r.user_id else None,
                "device_id": str(r.device_id) if r.device_id else None,
                "event_type": r.event_type,
                "feature": r.feature,
                "request_id": r.request_id,
                "metadata_json": r.metadata_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
