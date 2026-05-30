"""Device service — device lookup and listing."""

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


async def query_device_bind(
    *,
    db: AsyncSession,
    user_id: str,
    device_fingerprint: str,
) -> dict:
    """Look up a device by user + fingerprint. Returns device info if found.

    Raises ``ValueError("DEVICE_NOT_BOUND")`` if the device is not associated
    with this user.
    """
    fp_hash = hashlib.sha256(device_fingerprint.encode()).hexdigest()
    uid = uuid.UUID(user_id)

    result = await db.execute(
        select(Device).where(
            Device.user_id == uid,
            Device.device_fingerprint_hash == fp_hash,
        )
    )
    device: Device | None = result.scalar_one_or_none()

    if device is None:
        raise ValueError("DEVICE_NOT_BOUND")

    return {
        "device_id": str(device.id),
        "status": device.status,
        "device_name": device.device_name,
        "first_seen_at": device.first_seen_at.isoformat() if device.first_seen_at else None,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
    }


async def list_user_devices(
    *,
    db: AsyncSession,
    user_id: str,
) -> dict:
    """Return all devices belonging to *user_id* (no fingerprint hashes)."""
    uid = uuid.UUID(user_id)
    result = await db.execute(
        select(Device).where(Device.user_id == uid)
    )
    devices = result.scalars().all()

    return {
        "devices": [
            {
                "id": str(d.id),
                "device_name": d.device_name,
                "status": d.status,
                "first_seen_at": d.first_seen_at.isoformat() if d.first_seen_at else None,
                "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            }
            for d in devices
        ]
    }
