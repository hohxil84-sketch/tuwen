"""Auth API tests — login, refresh, logout.

Covers the test plan in ``docs/auth-device-plan.md`` section 7.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.security import generate_refresh_token, hash_password, hash_token
from app.models.auth_session import AuthSession

FINGERPRINT = "device-fingerprint-abc"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"

# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


class TestLogin:
    """Login endpoint tests."""

    async def test_login_success(self, client, test_user):
        """Correct credentials → 200 + token pair + user info."""
        res = await client.post(LOGIN_URL, json={
            "account": "test@example.com",
            "password": "correct-password",
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["error"] is None
        assert "request_id" in body
        data = body["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert data["user"]["account"] == "test@example.com"
        assert data["user"]["plan_code"] == "standard"
        assert data["device"]["status"] == "active"
        assert data["device"]["is_new"] is True

    async def test_login_wrong_password(self, client, test_user):
        """Wrong password → 401 INVALID_CREDENTIALS (anti-enumeration)."""
        res = await client.post(LOGIN_URL, json={
            "account": "test@example.com",
            "password": "wrong-password",
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 401, res.text
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_nonexistent_account(self, client):
        """Non-existent account → 401 INVALID_CREDENTIALS (same as wrong password)."""
        res = await client.post(LOGIN_URL, json={
            "account": "nobody@example.com",
            "password": "anything",
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 401, res.text
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_wrong_password_same_as_nonexistent(self, client, test_user):
        """Verify anti-enumeration: wrong password and non-existent user return
        the SAME error code and message."""
        # wrong password
        r1 = await client.post(LOGIN_URL, json={
            "account": "test@example.com",
            "password": "wrong-password",
            "device_fingerprint": FINGERPRINT,
        })
        # non-existent user
        r2 = await client.post(LOGIN_URL, json={
            "account": "ghost@example.com",
            "password": "whatever",
            "device_fingerprint": FINGERPRINT,
        })
        assert r1.status_code == r2.status_code == 401
        assert r1.json()["error"]["code"] == r2.json()["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_missing_fields(self, client):
        """Missing required fields → 422 with unified error format."""
        res = await client.post(LOGIN_URL, json={"account": "x"})
        assert res.status_code == 422
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Request validation failed"
        assert "errors" in body["error"]["details"]
        assert any(e["loc"] == ["body", "password"] for e in body["error"]["details"]["errors"])

    async def test_login_empty_device_fingerprint(self, client, test_user):
        """Empty device fingerprint → 422 with unified error format."""
        res = await client.post(LOGIN_URL, json={
            "account": "test@example.com",
            "password": "correct-password",
            "device_fingerprint": "",
        })
        assert res.status_code == 422
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Refresh tests
# ---------------------------------------------------------------------------


class TestRefresh:
    """Token refresh endpoint tests."""

    async def test_refresh_success(self, client, test_session):
        """Valid refresh_token → 200 + new token pair, old revoked."""
        session, plain = test_session

        res = await client.post(REFRESH_URL, json={
            "refresh_token": plain,
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["error"] is None
        data = body["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != plain  # rotated

        # Old token should now be revoked
        res2 = await client.post(REFRESH_URL, json={
            "refresh_token": plain,
            "device_fingerprint": FINGERPRINT,
        })
        assert res2.status_code == 401
        assert res2.json()["error"]["code"] == "TOKEN_REUSE"

    async def test_refresh_invalid_token(self, client):
        """Garbage token → 401."""
        res = await client.post(REFRESH_URL, json={
            "refresh_token": "not-a-valid-token",
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "REFRESH_INVALID"

    async def test_refresh_expired_token(self, client, db_session, test_user, test_device):
        """Expired refresh_token → 401 REFRESH_EXPIRED."""
        plain = generate_refresh_token()
        session = AuthSession(
            user_id=test_user.id,
            device_id=test_device.id,
            refresh_token_hash=hash_token(plain),
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        db_session.add(session)
        await db_session.flush()

        res = await client.post(REFRESH_URL, json={
            "refresh_token": plain,
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "REFRESH_EXPIRED"

    async def test_refresh_token_reuse_revokes_all(self, client, db_session, test_user, test_device):
        """Replay of a revoked token → TOKEN_REUSE, all user sessions revoked."""
        # Create two sessions
        p1, p2 = generate_refresh_token(), generate_refresh_token()
        s1 = AuthSession(
            user_id=test_user.id, device_id=test_device.id,
            refresh_token_hash=hash_token(p1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        s2 = AuthSession(
            user_id=test_user.id, device_id=test_device.id,
            refresh_token_hash=hash_token(p2),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add_all([s1, s2])
        await db_session.flush()

        # First refresh with p1 — succeeds
        r1 = await client.post(REFRESH_URL, json={
            "refresh_token": p1,
            "device_fingerprint": FINGERPRINT,
        })
        assert r1.status_code == 200

        # Replay p1 → TOKEN_REUSE
        r2 = await client.post(REFRESH_URL, json={
            "refresh_token": p1,
            "device_fingerprint": FINGERPRINT,
        })
        assert r2.status_code == 401
        assert r2.json()["error"]["code"] == "TOKEN_REUSE"

        # p2 should ALSO be revoked (all sessions for user)
        r3 = await client.post(REFRESH_URL, json={
            "refresh_token": p2,
            "device_fingerprint": FINGERPRINT,
        })
        assert r3.status_code == 401


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


class TestLogout:
    """Logout endpoint tests."""

    async def test_logout_revokes_token(self, client, test_session):
        """Logout with valid token → 200, token becomes invalid."""
        session, plain = test_session

        res = await client.post(LOGOUT_URL, json={"refresh_token": plain})
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["data"]["message"] == "logged out"

        # Token should now be revoked
        refresh_res = await client.post(REFRESH_URL, json={
            "refresh_token": plain,
            "device_fingerprint": FINGERPRINT,
        })
        assert refresh_res.status_code == 401

    async def test_logout_without_token(self, client):
        """Logout without providing a token → still 200 (client-side cleanup)."""
        res = await client.post(LOGOUT_URL, json={})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["message"] == "logged out"


# ---------------------------------------------------------------------------
# Device limit tests
# ---------------------------------------------------------------------------


class TestDeviceLimit:
    """3-device limit enforcement tests."""

    @pytest.mark.asyncio
    async def test_device_limit_reached(self, client, db_session, test_user):
        """4th unique device → 403 DEVICE_LIMIT_REACHED."""
        # Login with 3 distinct fingerprints
        for i in range(3):
            fp = f"device-fingerprint-{i}"
            res = await client.post(LOGIN_URL, json={
                "account": "test@example.com",
                "password": "correct-password",
                "device_fingerprint": fp,
            })
            assert res.status_code == 200, f"device {i} login failed: {res.text}"

        # 4th device should be rejected
        res = await client.post(LOGIN_URL, json={
            "account": "test@example.com",
            "password": "correct-password",
            "device_fingerprint": "device-fingerprint-4",
        })
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "DEVICE_LIMIT_REACHED"


# ---------------------------------------------------------------------------
# Disabled user tests
# ---------------------------------------------------------------------------


class TestDisabledUser:
    """User status enforcement tests."""

    @pytest.mark.asyncio
    async def test_disabled_user_login(self, client, db_session):
        """Disabled user → 403 USER_DISABLED."""
        from app.models.user import User

        user = User(
            id=uuid.uuid4(),
            account="disabled@example.com",
            password_hash=hash_password("password123"),
            plan_code="standard",
            status="disabled",
        )
        db_session.add(user)
        await db_session.flush()

        res = await client.post(LOGIN_URL, json={
            "account": "disabled@example.com",
            "password": "password123",
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "USER_DISABLED"
