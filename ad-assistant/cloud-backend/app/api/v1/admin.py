"""Admin API routes — 管理员操作（赠送积分等）."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.admin import AdminGrantRequest, AdminGrantResponse
from app.schemas.common import success_response
from app.services.credit_service import grant_credits

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.post(
    "/credits/grant",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def admin_grant_credits(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: AdminGrantRequest,
):
    """Admin grants credits to a specified user.

    Requires admin authentication (user ID in ADMIN_USER_IDS config).
    """
    # Validate target user_id
    try:
        target_user_id = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Invalid user_id: {body.user_id}",
            },
        )

    # Grant credits
    new_balance = await grant_credits(
        db=db,
        user_id=target_user_id,
        amount=body.amount,
        source_type="manual",
        source_id=str(admin.id),
        description=body.description or f"Admin grant by {admin.account}",
    )

    return success_response(
        data=AdminGrantResponse(
            user_id=str(target_user_id),
            amount=body.amount,
            new_balance=new_balance,
            description=body.description,
        ).model_dump()
    )
