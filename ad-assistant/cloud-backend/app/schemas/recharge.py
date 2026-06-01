"""Recharge / Order schemas — request/response DTOs."""

from pydantic import BaseModel, Field


class RechargeRequest(BaseModel):
    """Request to recharge / purchase a plan.

    Either *plan_code* or *amount_cny* must be provided.
    """

    plan_code: str | None = Field(
        default=None,
        description="Plan code to purchase (e.g. 'expert')",
    )
    amount_cny: int | None = Field(
        default=None,
        gt=0,
        description="Custom recharge amount in CNY",
    )


class RechargeResponse(BaseModel):
    """Response after a recharge (completed or pending)."""

    order_id: str
    plan_code: str | None
    amount_cny: int
    credits: int
    new_balance: int
    status: str
    payment_method: str
    plan_changed: bool = False


class OrderItem(BaseModel):
    """Single recharge order item."""

    id: str
    plan_code: str | None
    amount_cny: int
    credits: int
    payment_method: str
    status: str
    description: str | None
    created_at: str | None
    completed_at: str | None = None


class OrderListData(BaseModel):
    """Paginated order list response."""

    items: list[OrderItem]
    total: int
    limit: int
    offset: int
