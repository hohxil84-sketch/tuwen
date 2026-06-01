"""Sprint-04 Task-04: Recharge flow focused tests."""

import json
import uuid

import pytest
from sqlalchemy import func, select

from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.plan import Plan
from app.models.recharge_order import RechargeOrder
from app.services.credit_service import grant_credits
from app.services.plan_service import get_plan_by_code, list_active_plans
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
    """Build auth headers with a fresh access token for the test user."""
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
        """Granting credits increases user balance."""
        new_balance = await grant_credits(
            db=db_session,
            user_id=test_user.id,
            amount=100,
            source_type="system",
            description="Test grant",
        )
        assert new_balance == 100

        # Verify account updated
        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 100

    async def test_grant_creates_ledger_entry(self, db_session, test_user):
        """Grant writes a credit_ledger entry."""
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
        """Multiple grants accumulate correctly."""
        await grant_credits(db=db_session, user_id=test_user.id, amount=100, source_type="system")
        await grant_credits(db=db_session, user_id=test_user.id, amount=50, source_type="manual")

        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one()
        assert account.balance == 150

        # 2 ledger entries
        count = await db_session.execute(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.user_id == test_user.id)
        )
        assert count.scalar() == 2

    async def test_grant_zero_raises(self, db_session, test_user):
        """Amount <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="amount must be > 0"):
            await grant_credits(db=db_session, user_id=test_user.id, amount=0)

        with pytest.raises(ValueError, match="amount must be > 0"):
            await grant_credits(db=db_session, user_id=test_user.id, amount=-10)


# ---------------------------------------------------------------------------
# create_recharge_order
# ---------------------------------------------------------------------------


class TestRechargeOrder:
    """Recharge order creation with credit grant."""

    async def test_recharge_by_plan_code(self, db_session, test_user):
        """Recharging with a valid plan code creates order + grants credits."""
        await _seed_plan(db_session, code="basic", price_cny=99, monthly_credits=300)

        result = await create_recharge_order(
            db=db_session,
            user_id=test_user.id,
            plan_code="basic",
        )

        assert result["plan_code"] == "basic"
        assert result["amount_cny"] == 99
        assert result["credits"] == 300
        assert result["new_balance"] == 300
        assert result["status"] == "completed"

        # Verify order created
        order_result = await db_session.execute(
            select(RechargeOrder).where(RechargeOrder.user_id == test_user.id)
        )
        order = order_result.scalar_one()
        assert order.amount_cny == 99
        assert order.credits == 300

    async def test_recharge_by_custom_amount(self, db_session, test_user):
        """Custom amount recharge without a plan code."""
        result = await create_recharge_order(
            db=db_session,
            user_id=test_user.id,
            amount_cny=50,
        )

        assert result["plan_code"] is None
        assert result["amount_cny"] == 50
        assert result["credits"] == 5000  # 50 * 100
        assert result["new_balance"] == 5000

    async def test_recharge_invalid_plan_raises(self, db_session, test_user):
        """Non-existent plan raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await create_recharge_order(
                db=db_session,
                user_id=test_user.id,
                plan_code="nonexistent",
            )

    async def test_recharge_no_params_raises(self, db_session, test_user):
        """Missing both plan_code and amount_cny raises ValueError."""
        with pytest.raises(ValueError, match="Either plan_code or amount_cny"):
            await create_recharge_order(
                db=db_session,
                user_id=test_user.id,
            )

    async def test_recharge_negative_amount_raises(self, db_session, test_user):
        """Negative custom amount raises ValueError."""
        with pytest.raises(ValueError, match="amount_cny must be > 0"):
            await create_recharge_order(
                db=db_session,
                user_id=test_user.id,
                amount_cny=-10,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/credits/recharge (API integration)
# ---------------------------------------------------------------------------


class TestRechargeAPI:
    """API-level recharge endpoint tests."""

    async def test_recharge_success(
        self, client, db_session, test_user, test_device, test_session
    ):
        """POST /api/v1/credits/recharge with valid plan_code returns 200."""
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
        assert body["data"]["plan_code"] == "api_test"
        assert body["data"]["amount_cny"] == 199
        assert body["data"]["credits"] == 400
        assert body["data"]["new_balance"] == 400
        assert body["data"]["status"] == "completed"

    async def test_recharge_requires_auth(self, client, db_session):
        """Recharge without auth returns 401 (due to 6-step chain)."""
        resp = await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "test"},
        )
        assert resp.status_code == 401  # Missing Authorization header

    async def test_recharge_invalid_plan_returns_400(
        self, client, db_session, test_user, test_device, test_session
    ):
        """Recharge with invalid plan_code returns 400."""
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
        """Orders endpoint requires authentication."""
        resp = await client.get("/api/v1/orders")
        assert resp.status_code == 401

    async def test_orders_returns_empty_list(
        self, client, db_session, test_user, test_device, test_session
    ):
        """New user has no orders."""
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        resp = await client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    async def test_orders_includes_recharge(
        self, client, db_session, test_user, test_device, test_session
    ):
        """After a recharge, orders endpoint returns the order."""
        await _seed_plan(db_session, code="order_test", price_cny=88, monthly_credits=150)
        headers = await _auth_headers(client, db_session, test_user, test_device, test_session)

        # First, recharge
        await client.post(
            "/api/v1/credits/recharge",
            json={"plan_code": "order_test"},
            headers=headers,
        )

        # Then, check orders
        resp = await client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 1
        order = body["data"]["items"][0]
        assert order["amount_cny"] == 88
        assert order["credits"] == 150
        assert order["status"] == "completed"
