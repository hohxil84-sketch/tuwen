"""Provider call log schemas — request/response DTOs for provider_call_log."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProviderCallLogData(BaseModel):
    """单条 Provider 调用日志响应数据."""

    id: str
    request_id: str | None = None
    user_id: str | None = None
    device_id: str | None = None
    provider: str
    model: str
    feature: str
    status: str
    error_code: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float | None = None
    credits_charged: int | None = None
    latency_ms: int | None = None
    created_at: str | None = None


class ProviderCallLogListData(BaseModel):
    """Provider 调用日志列表响应数据."""

    items: list[ProviderCallLogData]
    total: int
    limit: int
    offset: int


class ProviderCallLogQueryParams(BaseModel):
    """Provider 调用日志查询参数."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    feature: str | None = None
    status: str | None = None
