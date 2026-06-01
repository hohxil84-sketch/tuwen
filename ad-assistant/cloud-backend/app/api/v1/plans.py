"""Plans API routes — 套餐查询（公开端点）."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import success_response
from app.schemas.plan import PlanListData, PlanResponse
from app.services.plan_service import list_active_plans

router = APIRouter(prefix="/api/v1", tags=["Plans"])


@router.get(
    "/plans",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_plans(
    db: AsyncSession = Depends(get_db),
):
    """List all active membership plans (no authentication required).

    Returns plans ordered by sort_order ascending.
    """
    plans = await list_active_plans(db=db)
    items = [PlanResponse.from_orm(p) for p in plans]
    return success_response(
        data=PlanListData(items=items, total=len(items)).model_dump()
    )
