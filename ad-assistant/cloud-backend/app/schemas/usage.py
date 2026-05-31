"""Usage event schemas — request/response DTOs for usage_events."""

from datetime import datetime

from pydantic import BaseModel, Field


class UsageEventData(BaseModel):
    """单条使用事件响应数据."""

    id: str
    user_id: str | None = None
    device_id: str | None = None
    event_type: str
    feature: str
    request_id: str | None = None
    metadata_json: dict | None = None
    created_at: str | None = None


class UsageEventListData(BaseModel):
    """使用事件列表响应数据."""

    items: list[UsageEventData]
    total: int
    limit: int
    offset: int


class UsageEventQueryParams(BaseModel):
    """使用事件查询参数."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    feature: str | None = None
