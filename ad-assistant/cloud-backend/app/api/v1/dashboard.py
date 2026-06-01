"""Dashboard API routes — Sprint-04 Task-02.

GET /api/v1/dashboard/summary — aggregated dashboard data for the authenticated user.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.dashboard import DashboardSummaryData
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get(
    "/dashboard/summary",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def dashboard_summary(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return aggregated dashboard data for the authenticated user.

    Includes credit balance, today's/monthly call counts, plan code, and
    the 5 most recent provider call log entries.
    """
    user, _device = user_and_device

    data = await get_dashboard_summary(db=db, user_id=user.id)
    return success_response(data=DashboardSummaryData(**data).model_dump())
