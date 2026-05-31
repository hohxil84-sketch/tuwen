"""Credit schemas — request/response DTOs for credit_accounts and credit_ledger."""

from pydantic import BaseModel, Field


class CreditBalanceResponse(BaseModel):
    """AI 算力余额响应."""

    user_id: str
    plan_code: str
    monthly_grant: int
    balance: int
    period_start: str | None = None
    period_end: str | None = None
    status: str
    updated_at: str | None = None


class CreditLedgerItem(BaseModel):
    """单条 AI 算力流水记录."""

    id: str
    user_id: str
    change_type: str
    amount: int
    balance_after: int
    source_type: str
    source_id: str | None = None
    description: str | None = None
    created_at: str | None = None


class CreditLedgerListData(BaseModel):
    """AI 算力流水列表响应."""

    items: list[CreditLedgerItem]
    total: int
    limit: int
    offset: int


class CreditLedgerQueryParams(BaseModel):
    """AI 算力流水查询参数."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
