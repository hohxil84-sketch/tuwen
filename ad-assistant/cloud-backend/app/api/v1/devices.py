"""Device routes — bind query and device listing.

See ``docs/api-draft-auth-device.md``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_with_device
from app.core.error_codes import ErrorCode
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.common import error_response, success_response
from app.schemas.device import BindData, BindQueryRequest, DeviceListData
from app.services.device_service import list_user_devices, query_device_bind

router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])


@router.post(
    "/bind",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def bind_device(
    body: BindQueryRequest,
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Query current device binding status.

    The device is auto-bound on first login — this endpoint only returns
    the current status.
    """
    user, _device = user_and_device

    try:
        data = await query_device_bind(
            db=db,
            user_id=str(user.id),
            device_fingerprint=body.device_fingerprint,
        )
        return success_response(data=BindData(**data).model_dump())
    except ValueError as exc:
        code = str(exc.args[0]) if exc.args else "UNKNOWN"
        if code == "DEVICE_NOT_BOUND":
            return JSONResponse(
                status_code=403,
                content=error_response(
                    code=ErrorCode.DEVICE_NOT_BOUND,
                    message="Device not bound to this user",
                ).model_dump(),
            )
        raise


@router.get(
    "/current",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def list_devices(
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all devices bound to the current user.

    Does NOT expose device fingerprint hashes.
    """
    user, _device = user_and_device
    data = await list_user_devices(db=db, user_id=str(user.id))
    return success_response(data=DeviceListData(**data).model_dump())
