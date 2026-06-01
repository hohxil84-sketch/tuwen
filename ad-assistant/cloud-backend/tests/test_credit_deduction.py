"""Sprint-03 Task-03: Real Credit Deduction focused tests.

Coverage:
- cny_to_credits: conversion, rounding up, zero, negative, configurable rate
- deduct_credits: success, partial deduction, zero amount, negative error
- execute_provider_call: deduction wiring, credits_charged populated,
  credit_ledger entry written, no user_id skip
- Integration: mock AI API credits_charged reflects actual deduction
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import Settings, settings
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.provider_call_log import ProviderCallLog
from app.providers.base import ProviderRequest
from app.providers.mock_provider import MockProvider
from app.services.cost_service import cny_to_credits
from app.services.credit_service import deduct_credits
from app.services.provider_service import (
    InsufficientBalanceError,
    execute_provider_call,
)
from app.services.provider_log_service import list_provider_call_logs


# ---------------------------------------------------------------------------
# 1. cny_to_credits
# ---------------------------------------------------------------------------


class TestCnyToCredits:
    """CNY → credits conversion with ceiling rounding."""

    def test_zero_cost_returns_zero(self):
        """Zero or negative cost → 0 credits."""
        assert cny_to_credits(0.0) == 0
        assert cny_to_credits(-0.01) == 0
        assert cny_to_credits(-999.0) == 0

    def test_small_cost_rounds_up_to_one(self):
        """Very small cost rounds UP to at least 1 credit."""
        assert cny_to_credits(0.001) == 1  # 0.1 → ceil → 1
        assert cny_to_credits(0.0001) == 1  # 0.01 → ceil → 1

    def test_exact_integer(self):
        """Cost that converts to exact integer."""
        # 0.10 CNY * 100 = 10.0 → ceil = 10
        assert cny_to_credits(0.10) == 10

    def test_rounds_up_not_down(self):
        """Ceiling: 0.009 CNY * 100 = 0.9 → ceil = 1, NOT 0."""
        assert cny_to_credits(0.009) == 1

    def test_moderate_cost(self):
        """Typical mock_ad_copy cost."""
        # Mock cost ≈ 0.09825 CNY → 9.825 → ceil = 10
        credits = cny_to_credits(0.09825)
        assert credits == 10

    def test_respects_configured_rate(self, monkeypatch):
        """Uses settings.CREDITS_PER_CNY, not a hardcoded constant."""
        monkeypatch.setattr(settings, "CREDITS_PER_CNY", 1000)
        # 0.001 CNY * 1000 = 1.0 → ceil = 1
        assert cny_to_credits(0.001) == 1
        # 0.0009 CNY * 1000 = 0.9 → ceil = 1
        assert cny_to_credits(0.0009) == 1


# ---------------------------------------------------------------------------
# 2. deduct_credits
# ---------------------------------------------------------------------------


class TestDeductCredits:
    """Atomic credit deduction."""

    @pytest.mark.anyio
    async def test_full_deduction(self, db_session, test_user):
        """Deduct credits when balance is sufficient."""
        # Give the user some credits
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=50, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        actual = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=10,
            source_id="req-test-1",
        )

        assert actual == 10
        # Balance should be reduced
        await db_session.refresh(account)
        assert account.balance == 40

    @pytest.mark.anyio
    async def test_partial_deduction_insufficient_balance(self, db_session, test_user):
        """When balance < amount, deduct only what's available."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=5, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        actual = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=100,
        )

        assert actual == 5  # Only 5 available
        await db_session.refresh(account)
        assert account.balance == 0

    @pytest.mark.anyio
    async def test_zero_balance_returns_zero(self, db_session, test_user):
        """Balance is 0 → deduct returns 0, no ledger entry."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=0, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        actual = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=10,
        )

        assert actual == 0
        await db_session.refresh(account)
        assert account.balance == 0

    @pytest.mark.anyio
    async def test_zero_amount_returns_zero(self, db_session, test_user):
        """amount=0 → no-op, returns 0."""
        actual = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=0,
        )
        assert actual == 0

    @pytest.mark.anyio
    async def test_negative_amount_raises(self, db_session, test_user):
        """Negative amount → ValueError."""
        with pytest.raises(ValueError, match="amount must be >= 0"):
            await deduct_credits(
                db=db_session, user_id=test_user.id, amount=-5,
            )

    @pytest.mark.anyio
    async def test_auto_creates_account_if_missing(self, db_session, test_user):
        """If user has no credit account yet, one is created with balance=0."""
        # User has no account → deduct returns 0, account is created
        actual = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=10,
        )
        assert actual == 0  # New account has 0 balance

        # Account should now exist
        result = await db_session.execute(
            select(CreditAccount).where(CreditAccount.user_id == test_user.id)
        )
        account = result.scalar_one_or_none()
        assert account is not None
        assert account.balance == 0

    @pytest.mark.anyio
    async def test_writes_credit_ledger_consume_entry(self, db_session, test_user):
        """Successful deduction writes a consume row to credit_ledger."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=30, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        await deduct_credits(
            db=db_session, user_id=test_user.id, amount=15,
            source_id="req-ledger-test",
            description="Test deduction",
        )

        # Verify the ledger entry
        rows = (
            await db_session.execute(
                select(CreditLedger)
                .where(CreditLedger.user_id == test_user.id)
                .order_by(CreditLedger.created_at.desc())
            )
        ).scalars().all()

        assert len(rows) >= 1
        entry = rows[0]
        assert entry.change_type == "consume"
        assert entry.amount == -15
        assert entry.balance_after == 15
        assert entry.source_type == "provider_call"
        assert entry.source_id == "req-ledger-test"
        assert "Test deduction" in entry.description
        assert entry.account_id == account.id


# ---------------------------------------------------------------------------
# 3. execute_provider_call + deduction
# ---------------------------------------------------------------------------


class TestProviderServiceWithDeduction:
    """Deduction is wired into execute_provider_call on success."""

    # MockProvider default usage (feature="mock_ad_copy" is not in its map):
    #   input_units=10, output_units=20, gpu_seconds=0.01
    #   cost = (10/1000)*0.035 + (20/1000)*0.11 + 0.01*1.2 = 0.01455
    #   credits = ceil(0.01455 * 100) = ceil(1.455) = 2

    @pytest.mark.anyio
    async def test_credits_charged_populated_on_success(self, db_session, test_user):
        """After a successful call, result.credits_charged is set."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=100, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        result = await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=uuid.uuid4(),
        )

        assert result.credits_charged > 0
        # Default usage → cost 0.01455 → ceil(1.455) = 2 credits
        assert result.credits_charged == 2

    @pytest.mark.anyio
    async def test_credit_ledger_entry_written(self, db_session, test_user):
        """Provider call writes a consume row to credit_ledger."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=100, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=uuid.uuid4(),
        )

        # Verify ledger
        rows = (
            await db_session.execute(
                select(CreditLedger)
                .where(CreditLedger.user_id == test_user.id)
                .order_by(CreditLedger.created_at.desc())
            )
        ).scalars().all()

        assert len(rows) >= 1
        entry = rows[0]
        assert entry.change_type == "consume"
        assert entry.amount == -2  # default usage → 2 credits
        assert entry.source_type == "provider_call"

    @pytest.mark.anyio
    async def test_balance_decreased(self, db_session, test_user):
        """Provider call decreases the user's credit balance."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=100, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=uuid.uuid4(),
        )

        await db_session.refresh(account)
        assert account.balance == 98  # 100 - 2

    @pytest.mark.anyio
    async def test_insufficient_balance_blocked_by_preflight(self, db_session, test_user):
        """Sprint-04: balance below FEATURE_MIN_CREDITS → InsufficientBalanceError."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=1, status="active",  # only 1 credit (< 2 min for mock_ad_copy)
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        with pytest.raises(InsufficientBalanceError) as exc_info:
            await execute_provider_call(
                db=db_session,
                provider=provider,
                request=request,
                user_id=test_user.id,
                device_id=uuid.uuid4(),
            )

        assert exc_info.value.error_code == "INSUFFICIENT_BALANCE"
        assert exc_info.value.required == 2  # FEATURE_MIN_CREDITS["mock_ad_copy"]
        assert exc_info.value.current == 1

        # Balance should NOT be touched
        await db_session.refresh(account)
        assert account.balance == 1

    @pytest.mark.anyio
    async def test_partial_deduction_when_above_min_but_below_cost(
        self, db_session, test_user, monkeypatch,
    ):
        """Partial deduction still works when balance passes pre-flight but
        falls short of actual cost (edge case: actual cost > estimated min)."""
        # Lower the feature minimum so pre-flight passes with balance=1
        monkeypatch.setitem(
            settings.FEATURE_MIN_CREDITS, "mock_ad_copy", 1,
        )

        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=1, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        result = await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=uuid.uuid4(),
        )

        # Partial deduction: cost ~2 credits, balance was 1
        assert result.credits_charged == 1
        await db_session.refresh(account)
        assert account.balance == 0

    @pytest.mark.anyio
    async def test_no_user_id_skips_deduction(self, db_session):
        """When user_id is None, no deduction occurs."""
        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        result = await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=None,  # System / internal call
            device_id=None,
        )

        assert result.credits_charged == 0

    @pytest.mark.anyio
    async def test_provider_call_log_credits_charged(self, db_session, test_user):
        """provider_call_log reflects the actual credits_charged."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=100, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="Test prompt")

        await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=uuid.uuid4(),
        )

        # Check provider_call_log
        rows = (
            await db_session.execute(
                select(ProviderCallLog)
                .where(ProviderCallLog.user_id == test_user.id)
                .order_by(ProviderCallLog.created_at.desc())
            )
        ).scalars().all()

        assert len(rows) >= 1
        assert rows[0].credits_charged == 2  # default usage → 2 credits
        assert rows[0].status == "success"
        assert rows[0].estimated_cost > 0


# ---------------------------------------------------------------------------
# 4. Concurrency guard — deduct_credits
# ---------------------------------------------------------------------------


class TestDeductCreditsConcurrency:
    """Verify conditional UPDATE prevents negative balance.

    SQLite (single-connection, no row-level locking in WAL) cannot truly
    replicate PostgreSQL concurrent-write behaviour, so these tests validate
    the conditional-UPDATE logic path (``WHERE balance >= :amount``) with
    sequential deductions that push the boundary.  PostgreSQL-level
    concurrency coverage lives in ``test_migrations_integration.py``.
    """

    @pytest.mark.anyio
    async def test_sequential_exhaustion_never_goes_negative(
        self, db_session, test_user,
    ):
        """Repeated deductions that sum past the balance must stop at 0."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=100, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        total_deducted = 0
        for i in range(6):
            d = await deduct_credits(
                db=db_session, user_id=test_user.id, amount=30,
                source_id=f"seq-{i}",
            )
            total_deducted += d

        # Total deducted must not exceed initial balance
        assert total_deducted <= 100, (
            f"Total deducted {total_deducted} exceeds initial balance 100"
        )
        await db_session.refresh(account)
        assert account.balance >= 0
        assert account.balance == 100 - total_deducted

    @pytest.mark.anyio
    async def test_conditional_update_rejects_insufficient(
        self, db_session, test_user,
    ):
        """When balance < amount, conditional UPDATE must not set negative."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=5, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        d = await deduct_credits(
            db=db_session, user_id=test_user.id, amount=100,
            source_id="reject-test",
        )

        # Should only deduct available 5, not 100
        assert d == 5
        await db_session.refresh(account)
        assert account.balance == 0

    @pytest.mark.anyio
    async def test_deductions_ledger_consistency(
        self, db_session, test_user,
    ):
        """Each deduction > 0 writes exactly one consume ledger entry."""
        account = CreditAccount(
            user_id=test_user.id, plan_code="standard", monthly_grant=0,
            balance=30, status="active",
        )
        db_session.add(account)
        await db_session.flush()

        results = []
        for i in range(3):
            d = await deduct_credits(
                db=db_session, user_id=test_user.id, amount=20,
                source_id=f"seq-{i}",
            )
            results.append(d)

        non_zero = [r for r in results if r > 0]
        ledger_count = await db_session.execute(
            select(func.count())
            .select_from(CreditLedger)
            .where(
                CreditLedger.user_id == test_user.id,
                CreditLedger.change_type == "consume",
            )
        )
        assert ledger_count.scalar() == len(non_zero)
