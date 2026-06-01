"""Auth service — login, token refresh, logout.

Implements the confirmed plan from ``docs/auth-device-plan.md``:

* Anti-enumeration: login failures return unified ``INVALID_CREDENTIALS``.
  Real reason (USER_NOT_FOUND / PASSWORD_WRONG) only in ``risk_logs.details``.
* Token rotation: refresh revokes old token, issues new pair.
* Token reuse detection: if a revoked token is replayed, ALL sessions for that
  user are revoked.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth_session import AuthSession
from app.models.device import Device
from app.models.risk_log import RiskLog
from app.models.user import User


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def login_user(
    *,
    db: AsyncSession,
    account: str,
    password: str,
    device_fingerprint: str,
    ip_hash: str | None = None,
) -> dict:
    """Authenticate a user and return token pair + user/device info.

    Raises ``ValueError`` with ``INVALID_CREDENTIALS`` if credentials are wrong.
    Raises ``ValueError`` with ``USER_DISABLED`` if user is not active.
    Raises ``ValueError`` with ``DEVICE_LIMIT_REACHED`` if device count exceeded.
    """
    device_fingerprint_hash = _fingerprint_hash(device_fingerprint)

    # 1. Look up user
    result = await db.execute(
        select(User).where(User.account == account)
    )
    user: User | None = result.scalar_one_or_none()

    if user is None:
        await _log_risk(
            db,
            user_id=None,
            device_id=None,
            ip_hash=ip_hash,
            event_type="LOGIN_FAILED",
            severity="low",
            details={
                "account": account,
                "reason": "USER_NOT_FOUND",
                "device_fingerprint_hash": device_fingerprint_hash,
            },
        )
        raise ValueError("INVALID_CREDENTIALS")

    # 2. Verify password
    if not verify_password(password, user.password_hash):
        await _log_risk(
            db,
            user_id=user.id,
            device_id=None,
            ip_hash=ip_hash,
            event_type="LOGIN_FAILED",
            severity="medium",
            details={
                "account": account,
                "reason": "PASSWORD_WRONG",
                "device_fingerprint_hash": device_fingerprint_hash,
            },
        )
        raise ValueError("INVALID_CREDENTIALS")

    # 3. Check user status
    if user.status != "active":
        raise ValueError("USER_DISABLED")

    # 4. Look up or create device
    device, is_new = await _find_or_create_device(
        db, user_id=user.id, fingerprint_hash=device_fingerprint_hash
    )

    # 5. Check device status
    if device.status == "banned":
        raise ValueError("DEVICE_BANNED")

    # 6. Check device limit (only for truly new devices)
    if is_new:
        count_result = await db.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.status == "active",
            )
        )
        active_devices = count_result.scalars().all()
        if len(active_devices) > settings.MAX_DEVICES_PER_USER:
            # Roll back the just-created device — mark as unbound
            device.status = "unbound"
            await db.flush()
            raise ValueError("DEVICE_LIMIT_REACHED")

    # Update device last_seen
    device.last_seen_at = datetime.now(timezone.utc)

    # 7. Issue tokens
    access_token = create_access_token(
        sub=str(user.id),
        device_id=str(device.id),
        plan=user.plan_code,
    )
    refresh_token = generate_refresh_token()
    refresh_token_hash = hash_token(refresh_token)

    # 8. Store session
    session = AuthSession(
        user_id=user.id,
        device_id=device.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS),
    )
    db.add(session)
    await db.flush()

    await _log_risk(
        db,
        user_id=user.id,
        device_id=device.id,
        ip_hash=ip_hash,
        event_type="LOGIN_SUCCESS",
        severity="low",
        details={"is_new_device": is_new},
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "user": {
            "id": str(user.id),
            "account": user.account,
            "plan_code": user.plan_code,
        },
        "device": {
            "id": str(device.id),
            "status": device.status,
            "is_new": is_new,
        },
    }


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

async def refresh_access_token(
    *,
    db: AsyncSession,
    refresh_token: str,
    device_fingerprint: str,
    ip_hash: str | None = None,
) -> dict:
    """Exchange a valid refresh_token for a new token pair.

    Rotates the token (old one revoked), and detects replay attacks.
    """
    token_hash = hash_token(refresh_token)

    # 1. Find session by token hash
    result = await db.execute(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == token_hash
        )
    )
    session: AuthSession | None = result.scalar_one_or_none()

    if session is None:
        raise ValueError("REFRESH_INVALID")

    # 2. Token reuse detection — already revoked
    if session.revoked_at is not None:
        # Replay attack → revoke ALL sessions for this user
        await db.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == session.user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await _log_risk(
            db,
            user_id=session.user_id,
            device_id=session.device_id,
            ip_hash=ip_hash,
            event_type="TOKEN_REUSE_DETECTED",
            severity="high",
            details={"session_id": str(session.id)},
        )
        raise ValueError("TOKEN_REUSE")

    # 3. Check expiry
    if session.expires_at < datetime.now(timezone.utc):
        raise ValueError("REFRESH_EXPIRED")

    # 4. Verify device (re-fetch to check ban status)
    device_result = await db.execute(
        select(Device).where(Device.id == session.device_id)
    )
    device: Device | None = device_result.scalar_one_or_none()
    if device is None or device.status == "banned":
        raise ValueError("DEVICE_BANNED")

    device_fingerprint_hash = _fingerprint_hash(device_fingerprint)
    if device.device_fingerprint_hash != device_fingerprint_hash:
        raise ValueError("DEVICE_NOT_BOUND")

    # 5. Revoke old session
    session.revoked_at = datetime.now(timezone.utc)

    # 6. Look up user for plan info
    user_result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user: User | None = user_result.scalar_one_or_none()
    if user is None or user.status != "active":
        raise ValueError("USER_DISABLED")

    # 7. Issue new tokens
    access_token = create_access_token(
        sub=str(user.id),
        device_id=str(device.id),
        plan=user.plan_code,
    )
    new_refresh_token = generate_refresh_token()
    new_token_hash = hash_token(new_refresh_token)

    new_session = AuthSession(
        user_id=user.id,
        device_id=device.id,
        refresh_token_hash=new_token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS),
    )
    db.add(new_session)
    await db.flush()

    # Update device last_seen
    device.last_seen_at = datetime.now(timezone.utc)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    }


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

async def logout_user(
    *,
    db: AsyncSession,
    refresh_token: str | None = None,
) -> dict:
    """Revoke the given refresh_token session (if provided)."""
    if refresh_token:
        token_hash = hash_token(refresh_token)
        result = await db.execute(
            select(AuthSession).where(
                AuthSession.refresh_token_hash == token_hash,
                AuthSession.revoked_at.is_(None),
            )
        )
        session: AuthSession | None = result.scalar_one_or_none()
        if session is not None:
            session.revoked_at = datetime.now(timezone.utc)

    return {"message": "logged out"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fingerprint_hash(raw: str) -> str:
    """Hash a device fingerprint with SHA-256 for privacy."""
    return hashlib.sha256(raw.encode()).hexdigest()


async def _find_or_create_device(
    db: AsyncSession, *, user_id, fingerprint_hash: str
) -> tuple[Device, bool]:
    """Return (device, is_new) for the given user + fingerprint."""
    result = await db.execute(
        select(Device).where(
            Device.user_id == user_id,
            Device.device_fingerprint_hash == fingerprint_hash,
        )
    )
    device = result.scalar_one_or_none()

    if device is not None:
        return device, False

    # Count current active devices for name
    count_result = await db.execute(
        select(Device).where(
            Device.user_id == user_id,
            Device.status == "active",
        )
    )
    active_count = len(count_result.scalars().all())

    device = Device(
        user_id=user_id,
        device_fingerprint_hash=fingerprint_hash,
        device_name=f"Device {active_count + 1}",
        status="active",
    )
    db.add(device)
    await db.flush()
    return device, True


async def _log_risk(
    db: AsyncSession,
    *,
    user_id,
    device_id,
    ip_hash: str | None,
    event_type: str,
    severity: str,
    details: dict | None = None,
) -> None:
    """Write a row to risk_logs.  Fire-and-forget — never raises."""
    try:
        db.add(
            RiskLog(
                user_id=user_id,
                device_id=device_id,
                ip_hash=ip_hash,
                event_type=event_type,
                severity=severity,
                details=details,
            )
        )
        await db.flush()
    except Exception:
        logging.exception(
            "risk_log write failed (non-fatal): user_id=%s event_type=%s",
            user_id,
            event_type,
        )
