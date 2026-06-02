"""S05-R02: Admin read-only query endpoint focused tests."""

import uuid

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.models.recharge_order import RechargeOrder
from app.models.credit_account import CreditAccount
from app.models.provider_call_log import ProviderCallLog
from app.models.usage_event import UsageEvent


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


async def _auth_headers(test_user, test_device, test_session):
    from app.core.security import create_access_token

    session, _plain = test_session
    token = create_access_token(
        sub=str(test_user.id),
        device_id=str(test_device.id),
        plan=test_user.plan_code,
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Forbidden (non-admin)
# ---------------------------------------------------------------------------


ENDPOINTS = [
    "/api/v1/admin/users",
    "/api/v1/admin/orders",
    "/api/v1/admin/credit-accounts",
    "/api/v1/admin/provider-logs",
    "/api/v1/admin/usage-events",
]


class TestAdminEndpointsForbidden:
    """Non-admin users must receive 403 on all admin query endpoints."""

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    async def test_non_admin_gets_403(
        self, client, db_session, test_user, test_device, test_session, endpoint
    ):
        headers = await _auth_headers(test_user, test_device, test_session)
        resp = await client.get(endpoint, headers=headers)
        assert resp.status_code == 403, (
            f"Expected 403 for {endpoint}, got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Admin access
# ---------------------------------------------------------------------------


class TestAdminEndpointsAuthorized:
    """Admin users can retrieve paginated lists."""

    @pytest.fixture(autouse=True)
    def _make_admin(self, monkeypatch):
        """Temporarily add test_user to admin whitelist."""
        monkeypatch.setattr(
            settings, "ADMIN_USER_IDS", ["__will_be_patched__"]
        )

    async def _patch_and_headers(self, monkeypatch, test_user, test_device, test_session):
        monkeypatch.setattr(
            settings, "ADMIN_USER_IDS", [str(test_user.id)]
        )
        return await _auth_headers(test_user, test_device, test_session)

    # -- users ----------------------------------------------------------------

    async def test_list_users_empty(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["items"] is not None
        # At least the test_user itself should be present
        accounts = [it["account"] for it in body["data"]["items"]]
        assert test_user.account in accounts
        # password_hash must never appear
        for item in body["data"]["items"]:
            assert "password_hash" not in item

    # -- orders ----------------------------------------------------------------

    async def test_list_orders(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get("/api/v1/admin/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)

    # -- credit-accounts ------------------------------------------------------

    async def test_list_credit_accounts(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get("/api/v1/admin/credit-accounts", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)

    # -- provider-logs --------------------------------------------------------

    async def test_list_provider_logs(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get("/api/v1/admin/provider-logs", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)
        # raw_usage / raw_response must never appear
        for item in body["data"]["items"]:
            assert "raw_usage" not in item
            assert "raw_response" not in item

    # -- usage-events ---------------------------------------------------------

    async def test_list_usage_events(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get("/api/v1/admin/usage-events", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)
        # metadata_json must never appear
        for item in body["data"]["items"]:
            assert "metadata_json" not in item

    # -- pagination -----------------------------------------------------------

    async def test_pagination_metadata(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get(
            "/api/v1/admin/users?limit=5&offset=0", headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert isinstance(data["total"], int)
        assert len(data["items"]) <= 5

    async def test_limit_capped_at_max(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        headers = await self._patch_and_headers(
            monkeypatch, test_user, test_device, test_session
        )
        resp = await client.get(
            "/api/v1/admin/users?limit=999", headers=headers
        )
        # limit=999 > MAX_LIMIT(100) → FastAPI should reject with 422
        assert resp.status_code == 422
