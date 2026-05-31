"""Usage event routes — query usage events for the authenticated user."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.usage import UsageEventListData, UsageEventQueryParams
from app.services.usage_service import list_usage_events

router = APIRouter(prefix="/api/v1/usage", tags=["Usage"])


@router.get(
    "/events",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_usage_events(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    feature: str | None = Query(default=None),
):
    """查询当前用户的使用事件列表（按时间倒序，支持分页和按 feature 筛选）。"""
    user, _device = user_and_device

    data = await list_usage_events(
        db=db,
        user_id=user.id,
        limit=limit,
        offset=offset,
        feature=feature,
    )
    return success_response(data=UsageEventListData(**data).model_dump())
