"""Provider call log routes — query call logs for the authenticated user."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.provider_log import ProviderCallLogListData
from app.services.provider_log_service import list_provider_call_logs

router = APIRouter(prefix="/api/v1", tags=["Provider Log"])


@router.get(
    "/provider-call-logs",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_provider_call_logs(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    feature: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
):
    """查询当前用户的 Provider 调用日志列表（按时间倒序，支持分页和筛选）。"""
    user, _device = user_and_device

    data = await list_provider_call_logs(
        db=db,
        user_id=user.id,
        limit=limit,
        offset=offset,
        feature=feature,
        status=status_filter,
    )
    return success_response(data=ProviderCallLogListData(**data).model_dump())
