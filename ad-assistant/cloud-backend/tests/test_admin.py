"""S05-R03: RBAC role-permission enforcement tests.

Tests cover:
- Non-admin (role="user") → 403 on all admin endpoints
- Admin role → 200 on all endpoints
- Operator role → 200 on read endpoints, 403 on credits/grant
- Bootstrap fallback (ADMIN_USER_IDS) still works
"""

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
# Endpoint / permission mapping
# ---------------------------------------------------------------------------

READ_ENDPOINTS = [
    ("/api/v1/admin/users", "users:read"),
    ("/api/v1/admin/orders", "orders:read"),
    ("/api/v1/admin/credit-accounts", "users:read"),
    ("/api/v1/admin/provider-logs", "provider_logs:read"),
    ("/api/v1/admin/usage-events", "usage_events:read"),
]

ALL_ENDPOINTS = [ep for ep, _ in READ_ENDPOINTS] + ["/api/v1/admin/credits/grant"]


# ---------------------------------------------------------------------------
# Forbidden — non-admin (role="user", not in ADMIN_USER_IDS)
# ---------------------------------------------------------------------------


class TestAdminEndpointsForbidden:
    """Default user (role="user") must receive 403 on all admin endpoints."""

    @pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
    async def test_non_admin_gets_403(
        self, client, db_session, test_user, test_device, test_session, endpoint
    ):
        headers = await _auth_headers(test_user, test_device, test_session)
        if endpoint == "/api/v1/admin/credits/grant":
            resp = await client.post(
                endpoint,
                headers=headers,
                json={
                    "user_id": str(test_user.id),
                    "amount": 10,
                    "description": "test",
                },
            )
        else:
            resp = await client.get(endpoint, headers=headers)
        assert resp.status_code == 403, (
            f"Expected 403 for {endpoint}, got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Admin role — full access
# ---------------------------------------------------------------------------


class TestAdminRoleFullAccess:
    """Admin role can access all endpoints."""

    @pytest.fixture(autouse=True)
    async def _set_admin_role(self, db_session, test_user):
        test_user.role = "admin"
        await db_session.flush()

    async def _headers(self, test_user, test_device, test_session):
        return await _auth_headers(test_user, test_device, test_session)

    # -- users ----------------------------------------------------------------

    async def test_list_users(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        accounts = [it["account"] for it in body["data"]["items"]]
        assert test_user.account in accounts
        # password_hash must never appear
        for item in body["data"]["items"]:
            assert "password_hash" not in item
            # role field should be present (S05-R03)
            assert "role" in item

    # -- orders ----------------------------------------------------------------

    async def test_list_orders(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)

    # -- credit-accounts ------------------------------------------------------

    async def test_list_credit_accounts(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/credit-accounts", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)

    # -- provider-logs --------------------------------------------------------

    async def test_list_provider_logs(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/provider-logs", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)
        for item in body["data"]["items"]:
            assert "raw_usage" not in item
            assert "raw_response" not in item

    # -- usage-events ---------------------------------------------------------

    async def test_list_usage_events(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/usage-events", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"]["items"], list)
        for item in body["data"]["items"]:
            assert "metadata_json" not in item

    # -- credits/grant --------------------------------------------------------

    async def test_grant_credits(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/credits/grant",
            headers=headers,
            json={
                "user_id": str(test_user.id),
                "amount": 10,
                "description": "admin grant test",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["amount"] == 10

    # -- pagination -----------------------------------------------------------

    async def test_pagination_metadata(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
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
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get(
            "/api/v1/admin/users?limit=999", headers=headers
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Operator role — read-only (no credits/grant)
# ---------------------------------------------------------------------------


class TestOperatorRoleReadOnly:
    """Operator can read but NOT grant credits."""

    @pytest.fixture(autouse=True)
    async def _set_operator_role(self, db_session, test_user):
        test_user.role = "operator"
        await db_session.flush()

    async def _headers(self, test_user, test_device, test_session):
        return await _auth_headers(test_user, test_device, test_session)

    @pytest.mark.parametrize("endpoint, _perm", READ_ENDPOINTS)
    async def test_operator_can_read(
        self, client, db_session, test_user, test_device, test_session, endpoint, _perm
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.get(endpoint, headers=headers)
        assert resp.status_code == 200, (
            f"Operator should be able to access {endpoint}, got {resp.status_code}: {resp.text}"
        )

    async def test_operator_cannot_grant(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await self._headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/credits/grant",
            headers=headers,
            json={
                "user_id": str(test_user.id),
                "amount": 10,
                "description": "operator should not grant",
            },
        )
        assert resp.status_code == 403, (
            f"Operator should NOT be able to grant credits, got {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Bootstrap fallback — ADMIN_USER_IDS still works even without role
# ---------------------------------------------------------------------------


class TestBootstrapFallback:
    """User in ADMIN_USER_IDS can access admin endpoints even with role='user'."""

    async def test_admin_ids_fallback_allows_access(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        # test_user has role="user" (default) but is in ADMIN_USER_IDS
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200, (
            f"Bootstrap fallback should allow access, got {resp.status_code}: {resp.text}"
        )

    async def test_admin_ids_fallback_allows_grant(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/credits/grant",
            headers=headers,
            json={
                "user_id": str(test_user.id),
                "amount": 5,
                "description": "bootstrap grant",
            },
        )
        assert resp.status_code == 200, resp.text

    async def test_admin_ids_empty_still_denies(
        self, client, db_session, test_user, test_device, test_session
    ):
        """With ADMIN_USER_IDS empty and role='user', access is denied."""
        # Default: role="user", ADMIN_USER_IDS=[]
        headers = await _auth_headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 403
