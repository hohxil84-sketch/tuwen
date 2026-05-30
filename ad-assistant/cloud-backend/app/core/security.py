"""Security utilities: password hashing, JWT creation / verification."""

import hashlib
import secrets
from datetime import datetime, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT (access token)
# ---------------------------------------------------------------------------

def create_access_token(*, sub: str, device_id: str, plan: str) -> str:
    """Issue a signed HS256 access token.

    ``sub`` is the user id (UUID string).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "device_id": device_id,
        "plan": plan,
        "iat": now,
        "exp": now.timestamp() + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate *token*.  Raises :class:`jwt.PyJWTError` on failure."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "device_id", "exp", "jti"]},
    )


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

def generate_refresh_token() -> str:
    """Return a cryptographically random URL-safe string (32 bytes → 43 chars)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return SHA-256 hex digest of *token* (for database storage)."""
    return hashlib.sha256(token.encode()).hexdigest()
