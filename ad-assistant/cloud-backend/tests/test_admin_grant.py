"""Sprint-04 Task-04: Admin grant API focused tests."""

import uuid

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.credit_account import CreditAccount


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


async def _auth_headers(client, db_session, test_user, test_device, test_session):
    from app.core.security import create_access_token

    session, _plain = test_session
    token = create_access_token(
        sub=str(test_user.id),
        device_id=str(test_device.id),
        plan=test_user.plan_code,
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /api/v1/admin/credits/grant
# ---------------------------------------------------------------------------


class TestAdminGrantAPI:
    """Admin grant credits to a user."""

    async def test_grant_forbidden_when_not_in_admin_list(
        self, client, db_session, test_user, test_device, test_session
    ):
        """User not in ADMIN_USER_IDS gets 403."""
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": str(test_user.id),
                "amount": 100,
                "description": "Test grant",
            },
            headers=headers,
        )

        # Either 403 (admin check) or 500 if ADMIN_USER_IDS is empty but config check catches
        assert resp.status_code in (403,)

    async def test_grant_succeeds_when_admin(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        """Admin in whitelist can grant credits."""
        # Make test_user an admin
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": str(test_user.id),
                "amount": 200,
                "description": "Welcome bonus",
            },
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["amount"] == 200
        assert body["data"]["new_balance"] == 200
        assert body["data"]["user_id"] == str(test_user.id)

        # Verify account updated
        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 200

    async def test_grant_another_user(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        """Admin can grant credits to another user."""
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        # Create another user
        from app.models.user import User
        from app.core.security import hash_password

        other_user = User(
            id=uuid.uuid4(),
            account="other@example.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": str(other_user.id),
                "amount": 500,
                "description": "Customer compensation",
            },
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["new_balance"] == 500

        # Verify the other user got the credits
        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == other_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 500

        # Admin's own account is untouched
        admin_result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        admin_account = admin_result.scalar_one_or_none()
        # Admin may not have a credit account if they haven't used credits
        if admin_account:
            assert admin_account.balance == 0

    async def test_grant_requires_auth(self, client, db_session):
        """Admin grant requires authentication."""
        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": str(uuid.uuid4()),
                "amount": 100,
            },
        )
        assert resp.status_code == 401

    async def test_grant_invalid_user_id_returns_400(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        """Invalid UUID in user_id returns 400."""
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": "not-a-valid-uuid",
                "amount": 100,
            },
            headers=headers,
        )

        assert resp.status_code == 400

    async def test_grant_zero_amount_returns_validation_error(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        """Zero or negative amount is rejected by Pydantic validation."""
        monkeypatch.setattr(settings, "ADMIN_USER_IDS", [str(test_user.id)])
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/admin/credits/grant",
            json={
                "user_id": str(test_user.id),
                "amount": 0,
            },
            headers=headers,
        )

        # Pydantic validation rejects gt=0
        assert resp.status_code == 422
