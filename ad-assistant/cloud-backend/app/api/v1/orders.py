"""Order API routes — 用户充值订单历史."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.database import get_db
from app.models.device import Device
from app.models.recharge_order import RechargeOrder
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.recharge import OrderItem, OrderListData

router = APIRouter(prefix="/api/v1", tags=["Orders"])


@router.get(
    "/orders",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_orders(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Return the authenticated user's recharge order history (paginated)."""
    user, _device = user_and_device

    # Count
    count_query = (
        select(func.count())
        .select_from(RechargeOrder)
        .where(RechargeOrder.user_id == user.id)
    )
    total = (await db.execute(count_query)).scalar() or 0

    # List
    query = (
        select(RechargeOrder)
        .where(RechargeOrder.user_id == user.id)
        .order_by(RechargeOrder.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    items = [
        OrderItem(
            id=str(r.id),
            plan_code=r.plan_code,
            amount_cny=r.amount_cny,
            credits=r.credits,
            payment_method=r.payment_method,
            status=r.status,
            description=r.description,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]

    return success_response(
        data=OrderListData(items=items, total=total, limit=limit, offset=offset).model_dump()
    )
