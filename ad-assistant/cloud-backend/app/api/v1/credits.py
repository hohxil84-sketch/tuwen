"""Credit API routes — 用户 AI 算力余额与流水查询（只读）+ 充值."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.credit import CreditBalanceResponse, CreditLedgerListData
from app.schemas.recharge import RechargeRequest, RechargeResponse
from app.services.credit_service import get_credit_balance, list_credit_ledger
from app.services.recharge_service import (
    DuplicateOrderError,
    InvalidRechargeAmountError,
    RateLimitExceededError,
    create_recharge_order,
)

router = APIRouter(prefix="/api/v1/credits", tags=["Credits"])


@router.get(
    "/balance",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_balance(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """查询当前登录用户的 AI 算力余额。

    若账户不存在，由 service 创建基础账户并返回余额 0。
    """
    user, _device = user_and_device
    data = await get_credit_balance(db=db, user_id=user.id)
    return success_response(data=CreditBalanceResponse(**data).model_dump())


@router.get(
    "/ledger",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def get_ledger(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """查询当前登录用户的 AI 算力流水（按时间倒序，支持分页）。"""
    user, _device = user_and_device
    data = await list_credit_ledger(db=db, user_id=user.id, limit=limit, offset=offset)
    return success_response(data=CreditLedgerListData(**data).model_dump())


@router.post(
    "/recharge",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def recharge_credits(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: RechargeRequest,
):
    """Recharge credits by purchasing a plan or custom amount.

    Either *plan_code* or *amount_cny* must be provided.
    Payment is simulated — credits are granted immediately.

    Pass an optional *idempotency_key* to prevent duplicate submissions:
    - Same key on a completed order → returns the existing order (200)
    - Same key on a pending order → 409 Conflict
    """
    user, _device = user_and_device

    try:
        result = await create_recharge_order(
            db=db,
            user_id=user.id,
            plan_code=body.plan_code,
            amount_cny=body.amount_cny,
            idempotency_key=body.idempotency_key,
        )
    except DuplicateOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_ORDER", "message": str(exc)},
        )
    except InvalidRechargeAmountError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_AMOUNT", "message": str(exc)},
        )
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": str(exc)},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(exc)},
        )

    return success_response(data=RechargeResponse(**result).model_dump())
