"""Device API tests — bind query and device listing."""

import pytest

from app.core.security import create_access_token
from app.models.device import Device

FINGERPRINT = "device-fingerprint-abc"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_header(test_user, test_device):
    """Build an Authorization header for the test user + device."""
    token = create_access_token(
        sub=str(test_user.id),
        device_id=str(test_device.id),
        plan=test_user.plan_code,
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Bind query tests
# ---------------------------------------------------------------------------


class TestBindDevice:
    """POST /api/v1/devices/bind tests."""

    async def test_bind_requires_auth(self, client):
        """No auth → 401."""
        res = await client.post("/api/v1/devices/bind", json={
            "device_fingerprint": FINGERPRINT,
        })
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_bind_success(self, client, test_user, test_device):
        """Valid auth + matching fingerprint → 200 with device info."""
        res = await client.post(
            "/api/v1/devices/bind",
            json={"device_fingerprint": FINGERPRINT},
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["device_id"] == str(test_device.id)
        assert body["data"]["status"] == "active"

    async def test_bind_device_not_found(self, client, test_user, test_device):
        """Fingerprint doesn't match any device → 403."""
        res = await client.post(
            "/api/v1/devices/bind",
            json={"device_fingerprint": "unknown-fingerprint"},
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "DEVICE_NOT_BOUND"

    async def test_bind_expired_token(self, client):
        """Expired token → 401."""
        res = await client.post(
            "/api/v1/devices/bind",
            json={"device_fingerprint": FINGERPRINT},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert "error" in body


# ---------------------------------------------------------------------------
# Device listing tests
# ---------------------------------------------------------------------------


class TestListDevices:
    """GET /api/v1/devices/current tests."""

    async def test_list_requires_auth(self, client):
        """No auth → 401."""
        res = await client.get("/api/v1/devices/current")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_list_success(self, client, test_user, test_device):
        """Returns all devices for the authenticated user."""
        res = await client.get(
            "/api/v1/devices/current",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["error"] is None
        assert "devices" in body["data"]
        devices = body["data"]["devices"]
        assert len(devices) >= 1
        assert any(d["id"] == str(test_device.id) for d in devices)

    async def test_list_no_fingerprints_exposed(self, client, test_user, test_device):
        """Device list must NOT contain fingerprint hashes."""
        res = await client.get(
            "/api/v1/devices/current",
            headers=_auth_header(test_user, test_device),
        )
        body = res.json()
        for d in body["data"]["devices"]:
            assert "fingerprint" not in d
            assert "device_fingerprint_hash" not in d

    async def test_list_invalid_token(self, client):
        """Invalid token → 401."""
        res = await client.get(
            "/api/v1/devices/current",
            headers={"Authorization": "Bearer garbage"},
        )
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert "error" in body


# ---------------------------------------------------------------------------
# Banned device tests
# ---------------------------------------------------------------------------


class TestBannedDevice:
    """Device status enforcement — banned devices should be denied."""

    async def test_banned_device_access(self, client, db_session, test_user):
        """A banned device should receive 403 on protected endpoints."""
        import hashlib
        import uuid

        fp = "banned-device-fingerprint"
        fp_hash = hashlib.sha256(fp.encode()).hexdigest()

        device = Device(
            id=uuid.uuid4(),
            user_id=test_user.id,
            device_fingerprint_hash=fp_hash,
            device_name="Banned Device",
            status="banned",
        )
        db_session.add(device)
        await db_session.flush()

        # Token with banned device_id
        token = create_access_token(
            sub=str(test_user.id),
            device_id=str(device.id),
            plan=test_user.plan_code,
        )

        res = await client.get(
            "/api/v1/devices/current",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "DEVICE_BANNED"
