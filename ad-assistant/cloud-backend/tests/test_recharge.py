"""Sprint-04 Task-04 rebuild + S05-R06 risk control tests.

Covers:
- grant_credits: atomic grant, ledger, edge cases
- create_recharge_order: plan purchase (simulated on/off), custom amount,
  plan_code update, plan_changed flag
- API integration: POST /api/v1/credits/recharge (auth, validation,
  pending vs completed)
- GET /api/v1/orders: auth, scoping, pagination
- (S05-R06) Idempotency: duplicate detection, replay, conflict
- (S05-R06) Amount validation: min/max
- (S05-R06) Rate limiting: sliding window
- (S05-R06) Order status machine: transition guards
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.plan import Plan
from app.models.recharge_order import (
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_PENDING,
    RechargeOrder,
)
from app.models.user import User
from app.services.credit_service import get_or_create_credit_account, grant_credits
from app.services.plan_service import get_plan_by_code
from app.services.recharge_service import (
    DuplicateOrderError,
    InvalidRechargeAmountError,
    InvalidStatusTransitionError,
    RateLimitExceededError,
    _check_rate_limit,
    _complete_order,
    _fail_order,
    _resolve_idempotency,
    _validate_amount,
    _validate_transition,
    create_recharge_order,
)


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
        with pytest.raises(InvalidRechargeAmountError, match="must be >="):
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


# ---------------------------------------------------------------------------
# S05-R06: Amount validation
# ---------------------------------------------------------------------------


class TestAmountValidation:
    """_validate_amount() unit tests."""

    def test_valid_amount_passes(self):
        _validate_amount(amount_cny=100)  # no exception

    def test_too_small_raises(self):
        with pytest.raises(InvalidRechargeAmountError, match="must be >="):
            _validate_amount(amount_cny=0)

    def test_negative_raises(self):
        with pytest.raises(InvalidRechargeAmountError, match="must be >="):
            _validate_amount(amount_cny=-50)

    def test_too_large_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "MAX_RECHARGE_AMOUNT_CNY", 5000)
        with pytest.raises(InvalidRechargeAmountError, match="must be <="):
            _validate_amount(amount_cny=5001)

    def test_max_boundary_passes(self, monkeypatch):
        monkeypatch.setattr(settings, "MAX_RECHARGE_AMOUNT_CNY", 5000)
        _validate_amount(amount_cny=5000)  # no exception

    def test_min_boundary_passes(self, monkeypatch):
        monkeypatch.setattr(settings, "MIN_RECHARGE_AMOUNT_CNY", 1)
        _validate_amount(amount_cny=1)  # no exception


# ---------------------------------------------------------------------------
# S05-R06: Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """_check_rate_limit() unit tests."""

    async def test_under_limit_passes(self, db_session, test_user):
        """No recent orders → rate limit check passes."""
        await _check_rate_limit(db=db_session, user_id=test_user.id)

    async def test_over_limit_raises(self, db_session, test_user, monkeypatch):
        """If recent order count >= threshold, raise RateLimitExceededError."""
        monkeypatch.setattr(settings, "RECHARGE_RATE_LIMIT_COUNT", 2)
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=10,
        )
        await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=20,
        )

        with pytest.raises(RateLimitExceededError, match="Rate limit exceeded"):
            await create_recharge_order(
                db=db_session, user_id=test_user.id, amount_cny=30,
            )

    async def test_rate_limit_respects_window(self, db_session, test_user, monkeypatch):
        """Orders outside the window should not count toward the limit."""
        monkeypatch.setattr(settings, "RECHARGE_RATE_LIMIT_COUNT", 2)
        monkeypatch.setattr(settings, "RECHARGE_RATE_LIMIT_WINDOW_SECONDS", 1)
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=10,
        )
        await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=20,
        )

        # Manually back-date the orders so they fall outside the window
        from datetime import timedelta
        result = await db_session.execute(
            select(RechargeOrder).where(RechargeOrder.user_id == test_user.id)
        )
        for order in result.scalars().all():
            order.created_at = order.created_at - timedelta(seconds=10)
        await db_session.flush()

        # Now the rate limit should pass
        await _check_rate_limit(db=db_session, user_id=test_user.id)

    async def test_other_user_orders_not_counted(
        self, db_session, test_user, monkeypatch,
    ):
        """Rate limit is per-user; other users' orders don't count."""
        monkeypatch.setattr(settings, "RECHARGE_RATE_LIMIT_COUNT", 1)
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        # Create another user
        from app.core.security import hash_password
        other_user = User(
            id=uuid.uuid4(),
            account="rl_other@test.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        # Other user creates an order
        await create_recharge_order(
            db=db_session, user_id=other_user.id, amount_cny=10,
        )

        # Test user should still be able to create an order
        await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=10,
        )


# ---------------------------------------------------------------------------
# S05-R06: Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Idempotency key tests — unit and service level."""

    async def test_no_key_skips_check(self, db_session, test_user):
        """idempotency_key=None → no dedup, normal creation."""
        result = await _resolve_idempotency(
            db=db_session, user_id=test_user.id, idempotency_key=None,
        )
        assert result is None

    async def test_new_key_returns_none(self, db_session, test_user):
        """A key not seen before → None (proceed to create)."""
        result = await _resolve_idempotency(
            db=db_session, user_id=test_user.id, idempotency_key="new-key-001",
        )
        assert result is None

    async def test_completed_order_replay(
        self, db_session, test_user, monkeypatch,
    ):
        """Same key on a COMPLETED order → return existing order."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        result1 = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=50,
            idempotency_key="idem-replay-001",
        )
        assert result1["status"] == "completed"
        assert result1["idempotent_replay"] is False

        # Second call with same key → idempotent replay
        result2 = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=50,
            idempotency_key="idem-replay-001",
        )
        assert result2["status"] == "completed"
        assert result2["idempotent_replay"] is True
        assert result2["order_id"] == result1["order_id"]
        # Balance should be the same (no double-credit)
        assert result2["new_balance"] == result1["new_balance"]

        # Only one order in DB
        count_result = await db_session.execute(
            select(func.count()).select_from(RechargeOrder).where(
                RechargeOrder.user_id == test_user.id,
                RechargeOrder.idempotency_key == "idem-replay-001",
            )
        )
        assert count_result.scalar() == 1

    async def test_pending_order_conflict(
        self, db_session, test_user,
    ):
        """Same key on a PENDING order → DuplicateOrderError."""
        # Create a pending order manually (simulated off = pending)
        order = RechargeOrder(
            user_id=test_user.id,
            amount_cny=50,
            credits=5000,
            status=ORDER_STATUS_PENDING,
            idempotency_key="idem-pending-001",
        )
        db_session.add(order)
        await db_session.flush()

        with pytest.raises(DuplicateOrderError, match="being processed"):
            await _resolve_idempotency(
                db=db_session, user_id=test_user.id,
                idempotency_key="idem-pending-001",
            )

    async def test_failed_order_allows_retry(
        self, db_session, test_user,
    ):
        """Same key on a FAILED order → None (allows retry with same key)."""
        order = RechargeOrder(
            user_id=test_user.id,
            amount_cny=50,
            credits=5000,
            status=ORDER_STATUS_FAILED,
            idempotency_key="idem-failed-001",
        )
        db_session.add(order)
        await db_session.flush()

        result = await _resolve_idempotency(
            db=db_session, user_id=test_user.id,
            idempotency_key="idem-failed-001",
        )
        assert result is None  # allows retry

    async def test_different_users_same_key_ok(
        self, db_session, test_user, monkeypatch,
    ):
        """Same idempotency_key for different users is allowed."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        # Test user creates order with key
        result1 = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=50,
            idempotency_key="shared-key",
        )

        # Different user with same key → new order
        from app.core.security import hash_password
        other_user = User(
            id=uuid.uuid4(),
            account="idem_other@test.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        result2 = await create_recharge_order(
            db=db_session, user_id=other_user.id, amount_cny=50,
            idempotency_key="shared-key",
        )

        assert result1["order_id"] != result2["order_id"]

    async def test_amount_mismatch_still_replays(
        self, db_session, test_user, monkeypatch,
    ):
        """Idempotent replay returns original order even if request params differ."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        result1 = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=100,
            idempotency_key="idem-mismatch",
        )

        # Different amount, same key → replay original
        result2 = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=999,
            idempotency_key="idem-mismatch",
        )
        assert result2["idempotent_replay"] is True
        assert result2["amount_cny"] == result1["amount_cny"]  # original amount

    async def test_failed_order_retry_creates_new_order(
        self, db_session, test_user, monkeypatch,
    ):
        """After a FAILED order, retry with same key creates a new order."""
        # Create a FAILED order
        failed = RechargeOrder(
            user_id=test_user.id,
            amount_cny=50,
            credits=5000,
            status=ORDER_STATUS_FAILED,
            idempotency_key="idem-retry-001",
        )
        db_session.add(failed)
        await db_session.flush()

        # Retry with same key and simulated payment on
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=50,
            idempotency_key="idem-retry-001",
        )

        assert result["status"] == "completed"
        assert result["idempotent_replay"] is False
        assert result["order_id"] != str(failed.id)

        # Two orders in DB (one FAILED, one COMPLETED)
        count_q = select(func.count()).select_from(RechargeOrder).where(
            RechargeOrder.user_id == test_user.id,
        )
        count = (await db_session.execute(count_q)).scalar()
        assert count == 2


# ---------------------------------------------------------------------------
# S05-R06: Order status machine
# ---------------------------------------------------------------------------


class TestOrderStatusMachine:
    """State transition guards and complete/fail helpers."""

    def test_valid_transition_pending_to_completed(self):
        _validate_transition(ORDER_STATUS_PENDING, ORDER_STATUS_COMPLETED)  # ok

    def test_valid_transition_pending_to_failed(self):
        _validate_transition(ORDER_STATUS_PENDING, ORDER_STATUS_FAILED)  # ok

    def test_invalid_transition_completed_to_anything(self):
        with pytest.raises(InvalidStatusTransitionError):
            _validate_transition(ORDER_STATUS_COMPLETED, ORDER_STATUS_PENDING)
        with pytest.raises(InvalidStatusTransitionError):
            _validate_transition(ORDER_STATUS_COMPLETED, ORDER_STATUS_FAILED)

    def test_invalid_transition_failed_to_anything(self):
        with pytest.raises(InvalidStatusTransitionError):
            _validate_transition(ORDER_STATUS_FAILED, ORDER_STATUS_PENDING)
        with pytest.raises(InvalidStatusTransitionError):
            _validate_transition(ORDER_STATUS_FAILED, ORDER_STATUS_COMPLETED)

    async def test_complete_order_sets_timestamp(
        self, db_session, test_user,
    ):
        """_complete_order() transitions status and sets completed_at."""
        order = RechargeOrder(
            user_id=test_user.id, amount_cny=10, credits=1000,
            status=ORDER_STATUS_PENDING,
        )
        db_session.add(order)
        await db_session.flush()

        await _complete_order(db=db_session, order=order)
        await db_session.flush()

        assert order.status == ORDER_STATUS_COMPLETED
        assert order.completed_at is not None

    async def test_fail_order_sets_timestamp(
        self, db_session, test_user,
    ):
        """_fail_order() transitions status and sets failed_at."""
        order = RechargeOrder(
            user_id=test_user.id, amount_cny=10, credits=1000,
            status=ORDER_STATUS_PENDING,
        )
        db_session.add(order)
        await db_session.flush()

        await _fail_order(db=db_session, order=order)
        await db_session.flush()

        assert order.status == ORDER_STATUS_FAILED
        assert order.failed_at is not None

    async def test_cannot_complete_already_completed(
        self, db_session, test_user,
    ):
        """Completing an already-completed order raises."""
        order = RechargeOrder(
            user_id=test_user.id, amount_cny=10, credits=1000,
            status=ORDER_STATUS_COMPLETED,
        )
        db_session.add(order)
        await db_session.flush()

        with pytest.raises(InvalidStatusTransitionError):
            await _complete_order(db=db_session, order=order)

    async def test_cannot_fail_already_failed(
        self, db_session, test_user,
    ):
        """Failing an already-failed order raises."""
        order = RechargeOrder(
            user_id=test_user.id, amount_cny=10, credits=1000,
            status=ORDER_STATUS_FAILED,
        )
        db_session.add(order)
        await db_session.flush()

        with pytest.raises(InvalidStatusTransitionError):
            await _fail_order(db=db_session, order=order)

    async def test_normal_recharge_creates_pending_then_completes(
        self, db_session, test_user, monkeypatch,
    ):
        """End-to-end: create_recharge_order → PENDING → COMPLETED."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)

        result = await create_recharge_order(
            db=db_session, user_id=test_user.id, amount_cny=25,
        )
        assert result["status"] == "completed"

        # Verify order in DB
        order_result = await db_session.execute(
            select(RechargeOrder).where(
                RechargeOrder.user_id == test_user.id,
            )
        )
        order = order_result.scalar_one()
        assert order.status == ORDER_STATUS_COMPLETED
        assert order.completed_at is not None


# ---------------------------------------------------------------------------
# S05-R06: API-level risk control integration
# ---------------------------------------------------------------------------


class TestRechargeRiskControlAPI:
    """API-level tests for risk control error responses."""

    async def _headers(self, client, db_session, test_user, test_device, test_session):
        from app.core.security import create_access_token
        session, _plain = test_session
        token = create_access_token(
            sub=str(test_user.id),
            device_id=str(test_device.id),
            plan=test_user.plan_code,
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_duplicate_pending_returns_409(
        self, client, db_session, test_user, test_device, test_session,
    ):
        """Idempotency collision on pending order → 409."""
        headers = await self._headers(
            client, db_session, test_user, test_device, test_session,
        )

        # First: pending (simulated off)
        resp1 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 50, "idempotency_key": "api-idem-001"},
            headers=headers,
        )
        assert resp1.status_code == 200

        # Second: same key → 409
        resp2 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 50, "idempotency_key": "api-idem-001"},
            headers=headers,
        )
        assert resp2.status_code == 409
        assert resp2.json()["error"]["code"] == "DUPLICATE_ORDER"

    async def test_idempotent_replay_returns_200(
        self, client, db_session, test_user, test_device, test_session, monkeypatch,
    ):
        """Same key on completed order → 200 with idempotent_replay=True."""
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        headers = await self._headers(
            client, db_session, test_user, test_device, test_session,
        )

        resp1 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 30, "idempotency_key": "api-replay-001"},
            headers=headers,
        )
        assert resp1.status_code == 200
        assert resp1.json()["data"]["idempotent_replay"] is False

        resp2 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 30, "idempotency_key": "api-replay-001"},
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["idempotent_replay"] is True

    async def test_invalid_amount_returns_400(
        self, client, db_session, test_user, test_device, test_session,
    ):
        """Amount > MAX → 400 INVALID_AMOUNT."""
        headers = await self._headers(
            client, db_session, test_user, test_device, test_session,
        )
        resp = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 999999},
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_AMOUNT"

    async def test_rate_limit_returns_429(
        self, client, db_session, test_user, test_device, test_session, monkeypatch,
    ):
        """Exceeding rate limit → 429."""
        monkeypatch.setattr(settings, "RECHARGE_RATE_LIMIT_COUNT", 1)
        monkeypatch.setattr(settings, "ENABLE_SIMULATED_PAYMENT", True)
        headers = await self._headers(
            client, db_session, test_user, test_device, test_session,
        )

        # First request: ok
        resp1 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 10},
            headers=headers,
        )
        assert resp1.status_code == 200

        # Second request: rate limited
        resp2 = await client.post(
            "/api/v1/credits/recharge",
            json={"amount_cny": 20},
            headers=headers,
        )
        assert resp2.status_code == 429
        assert resp2.json()["error"]["code"] == "RATE_LIMITED"
