"""Sprint-04 Task-04 rebuild: Recharge flow focused tests.

Covers:
- grant_credits: atomic grant, ledger, edge cases
- create_recharge_order: plan purchase (simulated on/off), custom amount,
  plan_code update, plan_changed flag
- API integration: POST /api/v1/credits/recharge (auth, validation,
  pending vs completed)
- GET /api/v1/orders: auth, scoping, pagination
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.plan import Plan
from app.models.recharge_order import RechargeOrder
from app.models.user import User
from app.services.credit_service import get_or_create_credit_account, grant_credits
from app.services.plan_service import get_plan_by_code
from app.services.recharge_service import create_recharge_order


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


async def _seed_plan(db_session, **overrides):
    defaults = {
        "name": "测试套餐",
        "code": "test_plan",
        "price_cny": 100,
        "monthly_credits": 200,
        "sort_order": 1,
        "status": "active",
    }
    defaults.update(overrides)
    plan = Plan(id=uuid.uuid4(), **defaults)
    db_session.add(plan)
    await db_session.flush()
    return plan


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
# grant_credits
# ---------------------------------------------------------------------------


class TestGrantCredits:
    """grant_credits() atomic credit grant."""

    async def test_grant_increases_balance(self, db_session, test_user):
        new_balance = await grant_credits(
            db=db_session,
            user_id=test_user.id,
            amount=100,
            source_type="system",
            description="Test grant",
        )
        assert new_balance == 100

        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 100

    async def test_grant_creates_ledger_entry(self, db_session, test_user):
        await grant_credits(
            db=db_session,
            user_id=test_user.id,
            amount=50,
            source_type="manual",
            description="Admin test",
        )

        result = await db_session.execute(
            select(CreditLedger).where(CreditLedger.user_id == test_user.id)
        )
        entries = result.scalars().all()
        assert len(entries) == 1
        assert entries[0].change_type == "grant"
        assert entries[0].amount == 50
        assert entries[0].source_type == "manual"
        assert entries[0].balance_after == 50

    async def test_grant_multiple_accumulates(self, db_session, test_user):
        await grant_credits(db=db_session, user_id=test_user.id, amount=100, source_type="system")
        await grant_credits(db=db_session, user_id=test_user.id, amount=50, source_type="manual")

        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 150

        count = await db_session.execute(
            select(func.count()).select_from(CreditLedger).where(
                CreditLedger.user_id == test_user.id
            )
        )
        assert count.scalar() == 2

    async def test_grant_zero_raises(self, db_session, test_user):
        with pytest.raises(ValueError, match="amount must be > 0"):
            await grant_credits(db=db_session, user_id=test_user.id, amount=0)

        with pytest.raises(ValueError, match="amount must be > 0"):
            await grant_credits(db=db_session, user_id=test_user.id, amount=-10)


# ---------------------------------------------------------------------------
# create_recharge_order — simulated ENABLED
# ---------------------------------------------------------------------------


class TestRechargeOrderSimulatedEnabled:
    """Recharge behaviour when ENABLE_SIMULATED_PAYMENT=True."""

    async def test_recharge_by_plan_creates_completed_order(
        self, db_session, test_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="basic", price_cny=99, monthly_credits=300)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="basic",
        )

        assert result["status"] == "completed"
        assert result["payment_method"] == "simulated"
        assert result["plan_code"] == "basic"
        assert result["amount_cny"] == 99
        assert result["credits"] == 300
        assert result["new_balance"] == 300
        assert result["plan_changed"] is True  # user was "standard", now "basic"

    async def test_recharge_updates_user_plan_code(
        self, db_session, test_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="expert", price_cny=559, monthly_credits=1000)

        assert test_user.plan_code == "standard"

        await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="expert",
        )

        await db_session.refresh(test_user)
        assert test_user.plan_code == "expert"

    async def test_recharge_updates_credit_account_plan_code(
        self, db_session, test_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="expert", price_cny=559, monthly_credits=1000)

        # Ensure credit account exists
        await get_or_create_credit_account(db=db_session, user_id=test_user.id)

        await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="expert",
        )

        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.plan_code == "expert"

    async def test_recharge_same_plan_no_change(
        self, db_session, test_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="standard", price_cny=359, monthly_credits=500)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="standard",
        )

        assert result["plan_changed"] is False

    async def test_recharge_by_custom_amount(self, db_session, test_user, monkeypatch):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=50,
        )

        assert result["plan_code"] is None
        assert result["plan_changed"] is False
        assert result["amount_cny"] == 50
        assert result["credits"] == 5000  # 50 * CREDITS_PER_CNY (100)
        assert result["new_balance"] == 5000

    async def test_recharge_writes_ledger(self, db_session, test_user, monkeypatch):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="basic", price_cny=99, monthly_credits=300)

        await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="basic",
        )

        result = await db_session.execute(
            select(CreditLedger).where(CreditLedger.user_id == test_user.id)
        )
        entries = result.scalars().all()
        assert len(entries) == 1
        assert entries[0].change_type == "grant"
        assert entries[0].source_type == "order"

    async def test_recharge_invalid_plan_raises(self, db_session, test_user, monkeypatch):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        with pytest.raises(ValueError, match="not found"):
            await create_recharge_order(
                db=db_session, user_id=test_user.id, plan_code="nonexistent",
            )

    async def test_recharge_no_params_raises(self, db_session, test_user):
        with pytest.raises(ValueError, match="Either plan_code or amount_cny"):
            await create_recharge_order(db=db_session, user_id=test_user.id)

    async def test_recharge_negative_amount_raises(self, db_session, test_user):
        with pytest.raises(ValueError, match="amount_cny must be > 0"):
            await create_recharge_order(
                db=db_session, user_id=test_user.id, amount_cny=-10,
            )


# ---------------------------------------------------------------------------
# create_recharge_order — simulated DISABLED
# ---------------------------------------------------------------------------


class TestRechargeOrderSimulatedDisabled:
    """Recharge behaviour when ENABLE_SIMULATED_PAYMENT=False (default)."""

    async def test_recharge_creates_pending_order(self, db_session, test_user):
        """With simulated off, order is pending and no credits are granted."""
        await _seed_plan(db_session, code="basic", price_cny=99, monthly_credits=300)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="basic",
        )

        assert result["status"] == "pending"
        assert result["new_balance"] == 0  # no credits granted
        assert result["plan_changed"] is False  # plan unchanged when pending

        # Verify order in DB
        order_result = await db_session.execute(
            select(RechargeOrder).where(RechargeOrder.user_id == test_user.id)
        )
        order = order_result.scalar_one()
        assert order.status == "pending"
        assert order.completed_at is None

    async def test_recharge_pending_does_not_update_plan(
        self, db_session, test_user
    ):
        """When payment is pending, plan_code must NOT change."""
        await _seed_plan(db_session, code="expert", price_cny=559, monthly_credits=1000)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="expert",
        )

        assert result["plan_changed"] is False
        await db_session.refresh(test_user)
        assert test_user.plan_code == "standard"  # unchanged

    async def test_recharge_pending_no_ledger(self, db_session, test_user):
        """Pending order should NOT write a credit ledger entry."""
        await _seed_plan(db_session, code="basic", price_cny=99, monthly_credits=300)

        await create_recharge_order(
            db=db_session, user_id=test_user.id, plan_code="basic",
        )

        count = await db_session.execute(
            select(func.count()).select_from(CreditLedger).where(
                CreditLedger.user_id == test_user.id
            )
        )
        assert count.scalar() == 0


# ---------------------------------------------------------------------------
# POST /api/v1/credits/recharge (API integration)
# ---------------------------------------------------------------------------


class TestRechargeAPI:
    """API-level recharge endpoint tests."""

    async def test_recharge_success_simulated_enabled(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="api_test", price_cny=199, monthly_credits=400)
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "api_test"},
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "completed"
        assert body["data"]["plan_changed"] is True
        assert body["data"]["payment_method"] == "simulated"
        assert body["data"]["amount_cny"] == 199
        assert body["data"]["credits"] == 400

    async def test_recharge_pending_when_simulated_disabled(
        self, client, db_session, test_user, test_device, test_session
    ):
        """Default config: ENABLE_SIMULATED_PAYMENT=False → pending order."""
        await _seed_plan(db_session, code="api_test", price_cny=199, monthly_credits=400)
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "api_test"},
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "pending"
        assert body["data"]["new_balance"] == 0
        assert body["data"]["plan_changed"] is False

    async def test_recharge_requires_auth(self, client, db_session):
        resp = await client.post(
            "/api/v1/credits/recharge", json={"plan_code": "test"},
        )
        assert resp.status_code == 401

    async def test_recharge_invalid_plan_returns_400(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "no_such_plan"},
            headers=headers,
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/orders (API integration)
# ---------------------------------------------------------------------------


class TestOrdersAPI:
    """API-level orders listing endpoint tests."""

    async def test_orders_requires_auth(self, client, db_session):
        resp = await client.get("/api/v1/orders")
        assert resp.status_code == 401

    async def test_orders_returns_empty_list(
        self, client, db_session, test_user, test_device, test_session
    ):
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)
        resp = await client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    async def test_orders_includes_recharge(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="order_test", price_cny=88, monthly_credits=150)
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "order_test"},
            headers=headers,
        )

        resp = await client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 1
        order = body["data"]["items"][0]
        assert order["amount_cny"] == 88
        assert order["credits"] == 150
        assert order["status"] == "completed"
        assert "payment_method" in order
        assert "completed_at" in order

    async def test_orders_scoped_to_user(
        self, client, db_session, test_user, test_device, test_session, monkeypatch
    ):
        """User A cannot see User B's orders."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        await _seed_plan(db_session, code="scoped", price_cny=50, monthly_credits=100)

        # Create another user
        from app.core.security import hash_password
        other_user = User(
            id=uuid.uuid4(),
            account="other@test.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        # Other user recharges
        await create_recharge_order(
            db=db_session, user_id=other_user.id, plan_code="scoped",
        )

        # Test user checks orders — should be empty
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)
        resp = await client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0
