"""Admin schemas — request/response DTOs for admin operations."""

from pydantic import BaseModel, Field


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
