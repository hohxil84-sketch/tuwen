"""S05-R04: Monthly credit grant service tests.

Tests cover:
- Idempotency: same user + same month → only one grant
- Cross-month: same user + different months → separate grants
- Eligibility: active users only, plan with monthly_credits > 0
- Balance verification
- Dry-run mode
- Empty dataset
"""

import uuid

import pytest
from sqlalchemy import select

from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.plan import Plan
from app.services.monthly_grant_service import (
    GRANT_SOURCE_TYPE,
    GrantSummary,
    _make_source_id,
    _already_granted,
    grant_monthly_credits_for_user,
    process_monthly_grants,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_credit_account(db_session, user, plan_code="standard"):
    """Create a credit account for *user* if they don't have one yet."""
    result = await db_session.execute(
        select(CreditAccount).where(CreditAccount.user_id == user.id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = CreditAccount(
            user_id=user.id,
            plan_code=plan_code,
            balance=0,
            monthly_grant=0,
            status="active",
        )
        db_session.add(account)
        await db_session.flush()
    return account


async def _ensure_plan(db_session, code="standard", monthly_credits=100):
    """Create or update a plan with the given code."""
    result = await db_session.execute(
        select(Plan).where(Plan.code == code)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        plan = Plan(
            id=uuid.uuid4(),
            name=code.title(),
            code=code,
            price_cny=19900,
            monthly_credits=monthly_credits,
            status="active",
        )
        db_session.add(plan)
        await db_session.flush()
    else:
        plan.monthly_credits = monthly_credits
        await db_session.flush()
    return plan


# ---------------------------------------------------------------------------
# Idempotency key
# ---------------------------------------------------------------------------


class TestSourceId:
    def test_format(self):
        uid = uuid.UUID("12345678-1234-1234-1234-123456789abc")
        assert _make_source_id(uid, 2026, 6) == "12345678-1234-1234-1234-123456789abc:2026-06"

    def test_zero_padded_month(self):
        uid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        assert _make_source_id(uid, 2026, 1) == "00000000-0000-0000-0000-000000000001:2026-01"


# ---------------------------------------------------------------------------
# Single-user grant
# ---------------------------------------------------------------------------


class TestGrantMonthlyCreditsForUser:
    async def test_grants_successfully(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        granted, error = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 6,
        )
        assert granted is True
        assert error is None

        # Verify balance increased
        account = await _ensure_credit_account(db_session, test_user)
        await db_session.refresh(account)
        assert account.balance == 100

        # Verify ledger entry exists
        source_id = _make_source_id(test_user.id, 2026, 6)
        result = await db_session.execute(
            select(CreditLedger).where(
                CreditLedger.user_id == test_user.id,
                CreditLedger.source_type == GRANT_SOURCE_TYPE,
                CreditLedger.source_id == source_id,
            )
        )
        ledger = result.scalar_one_or_none()
        assert ledger is not None
        assert ledger.amount == 100
        assert ledger.change_type == "grant"

    async def test_idempotent(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        # First grant
        g1, e1 = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 6,
        )
        assert g1 is True
        assert e1 is None

        # Second grant (same month)
        g2, e2 = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 6,
        )
        assert g2 is False  # skipped
        assert e2 is None

        # Balance should still be 100 (not 200)
        account = await _ensure_credit_account(db_session, test_user)
        await db_session.refresh(account)
        assert account.balance == 100

    async def test_different_months(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        # Grant June
        g1, _ = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 6,
        )
        assert g1 is True

        # Grant July
        g2, _ = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 7,
        )
        assert g2 is True

        # Balance should be 200
        account = await _ensure_credit_account(db_session, test_user)
        await db_session.refresh(account)
        assert account.balance == 200

    async def test_dry_run_no_write(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        granted, error = await grant_monthly_credits_for_user(
            db_session, test_user, plan, 2026, 6, dry_run=True,
        )
        assert granted is True  # would grant
        assert error is None

        # Balance should NOT have changed
        account = await _ensure_credit_account(db_session, test_user)
        await db_session.refresh(account)
        assert account.balance == 0

        # No ledger entry written
        source_id = _make_source_id(test_user.id, 2026, 6)
        assert await _already_granted(db_session, test_user.id, source_id) is False


# ---------------------------------------------------------------------------
# Batch orchestrator
# ---------------------------------------------------------------------------


class TestProcessMonthlyGrants:
    async def test_empty_dataset(
        self, db_session,
    ):
        # No plans with monthly_credits
        summary = await process_monthly_grants(db_session, 2026, 6)
        assert isinstance(summary, GrantSummary)
        assert summary.granted == 0
        assert summary.skipped == 0
        assert summary.failed == 0

    async def test_eligible_user_gets_grant(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        summary = await process_monthly_grants(db_session, 2026, 6)
        assert summary.granted == 1
        assert summary.skipped == 0
        assert summary.failed == 0
        assert summary.errors == []

    async def test_inactive_user_skipped(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)
        test_user.status = "disabled"
        await db_session.flush()

        summary = await process_monthly_grants(db_session, 2026, 6)
        assert summary.granted == 0
        assert summary.skipped == 0  # not even queried

    async def test_plan_without_monthly_credits_skipped(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=0)
        await _ensure_credit_account(db_session, test_user, plan.code)

        summary = await process_monthly_grants(db_session, 2026, 6)
        assert summary.granted == 0
        assert summary.skipped == 0  # plan has monthly_credits=0, excluded from query

    async def test_already_granted_skipped(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        # First run
        s1 = await process_monthly_grants(db_session, 2026, 6)
        assert s1.granted == 1
        assert s1.skipped == 0

        # Second run (same month)
        s2 = await process_monthly_grants(db_session, 2026, 6)
        assert s2.granted == 0
        assert s2.skipped == 1

    async def test_dry_run(
        self, db_session, test_user,
    ):
        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        summary = await process_monthly_grants(db_session, 2026, 6, dry_run=True)
        assert summary.granted == 1
        assert summary.failed == 0

        # Balance should NOT have changed
        account = await _ensure_credit_account(db_session, test_user)
        await db_session.refresh(account)
        assert account.balance == 0


# ---------------------------------------------------------------------------
# Admin endpoint
# ---------------------------------------------------------------------------


class TestAdminMonthlyGrantEndpoint:
    async def _auth_headers(self, test_user, test_device, test_session):
        from app.core.security import create_access_token
        session, _plain = test_session
        token = create_access_token(
            sub=str(test_user.id),
            device_id=str(test_device.id),
            plan=test_user.plan_code,
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_admin_can_trigger(
        self, client, db_session, test_user, test_device, test_session,
    ):
        # Make test_user admin
        test_user.role = "admin"
        await db_session.flush()

        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/monthly-grant/run",
            headers=headers,
            json={"year": 2026, "month": 6},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["granted"] >= 1
        assert body["data"]["failed"] == 0

    async def test_non_admin_gets_403(
        self, client, db_session, test_user, test_device, test_session,
    ):
        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/monthly-grant/run",
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_operator_cannot_trigger(
        self, client, db_session, test_user, test_device, test_session,
    ):
        test_user.role = "operator"
        await db_session.flush()

        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.post(
            "/api/v1/admin/monthly-grant/run",
            headers=headers,
        )
        assert resp.status_code == 403, (
            f"Operator should not have credits:grant, got {resp.status_code}"
        )

    async def test_defaults_to_current_month(
        self, client, db_session, test_user, test_device, test_session,
    ):
        test_user.role = "admin"
        await db_session.flush()

        plan = await _ensure_plan(db_session, monthly_credits=100)
        await _ensure_credit_account(db_session, test_user, plan.code)

        headers = await self._auth_headers(test_user, test_device, test_session)
        # No body → defaults to current UTC month
        resp = await client.post(
            "/api/v1/admin/monthly-grant/run",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
