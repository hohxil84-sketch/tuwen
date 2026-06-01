"""Dashboard aggregation schemas — Sprint-04 Task-02."""

from pydantic import BaseModel, Field


class RecentActivityItem(BaseModel):
    """A single row in the dashboard recent-activity list."""

    feature: str
    provider: str
    model: str
    status: str
    credits_charged: int = 0
    created_at: str  # ISO-8601


class DashboardSummaryData(BaseModel):
    """Aggregated dashboard summary returned by GET /api/v1/dashboard/summary."""

    credit_balance: int = Field(default=0, description="Current AI credit balance")
    today_calls: int = Field(default=0, description="Successful provider calls today (UTC)")
    monthly_calls: int = Field(default=0, description="Successful provider calls this month (UTC)")
    plan_code: str = Field(default="standard", description="User's current plan code")
    recent_activity: list[RecentActivityItem] = Field(
        default_factory=list, description="Up to 5 most recent provider call log entries"
    )
