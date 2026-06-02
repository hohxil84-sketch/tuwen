"""Admin schemas — request/response DTOs for admin operations."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Admin Grant (S04-T04 — existing)
# ---------------------------------------------------------------------------


class AdminGrantRequest(BaseModel):
    """Admin grant credits to a user."""

    user_id: str = Field(..., description="Target user UUID")
    amount: int = Field(..., gt=0, description="Credits to grant")
    description: str | None = Field(
        default=None, description="Reason for the grant"
    )


class AdminGrantResponse(BaseModel):
    """Response after a successful admin grant."""

    user_id: str
    amount: int
    new_balance: int
    description: str | None


# ---------------------------------------------------------------------------
# Pagination (S05-R02)
# ---------------------------------------------------------------------------


class PaginatedItems(BaseModel):
    """Shared pagination wrapper for admin list endpoints."""

    items: list
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Admin list item schemas (S05-R02)
# ---------------------------------------------------------------------------


class AdminUserItem(BaseModel):
    """Public-safe user row for admin listing."""

    id: str
    account: str
    plan_code: str
    role: str
    status: str
    created_at: datetime | None

    model_config = {"from_attributes": True}


class AdminOrderItem(BaseModel):
    """Recharge order row for admin listing."""

    id: str
    user_id: str
    plan_code: str | None
    amount_cny: int
    credits: int
    payment_method: str
    status: str
    description: str | None
    created_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AdminCreditAccountItem(BaseModel):
    """Credit account row for admin listing."""

    id: str
    user_id: str
    plan_code: str
    balance: int
    monthly_grant: int
    status: str
    created_at: datetime | None

    model_config = {"from_attributes": True}


class AdminProviderLogItem(BaseModel):
    """Provider call log row for admin listing (no raw payload)."""

    id: str
    request_id: str | None
    user_id: str | None
    provider: str
    model: str
    feature: str
    status: str
    error_code: str | None
    total_tokens: int
    credits_charged: int | None
    latency_ms: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class AdminUsageEventItem(BaseModel):
    """Usage event row for admin listing (no metadata_json)."""

    id: str
    user_id: str | None
    event_type: str
    feature: str
    request_id: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Monthly grant (S05-R04)
# ---------------------------------------------------------------------------


class MonthlyGrantRequest(BaseModel):
    """Optional target year/month for manual monthly grant trigger."""

    year: int | None = Field(default=None, ge=2024, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)


class MonthlyGrantResponse(BaseModel):
    """Summary after a monthly grant run."""

    granted: int
    skipped: int
    failed: int
    errors: list[dict]


# ---------------------------------------------------------------------------
# Provider health (S05-R05)
# ---------------------------------------------------------------------------


class ProviderHealthItem(BaseModel):
    """Circuit breaker status for a single provider."""

    state: str  # "CLOSED" | "OPEN" | "HALF_OPEN"
    consecutive_failures: int
    opened_at: float | None


class ProviderHealthResponse(BaseModel):
    """Health status for all registered providers."""

    providers: dict[str, ProviderHealthItem]
