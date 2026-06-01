"""Sprint-04 Task-01: Provider Reliability focused tests.

Coverage:
- Part A: Pre-flight balance check (two-level gate)
- Part B: Provider fallback chain + retry logic
- Part C: Router.resolve_name + registry property
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.provider_call_log import ProviderCallLog
from app.providers.base import ProviderRequest
from app.providers.deepseek_provider import DeepSeekProviderError
from app.providers.mock_provider import MockProvider, MockProviderError
from app.providers.registry import ProviderRegistry, get_provider_registry
from app.providers.router import ProviderRouter, get_provider_router
from app.services.provider_service import (
    FALLBACK_RULES,
    InsufficientBalanceError,
    _check_balance,
    _is_retryable,
    execute_provider_call,
    route_and_execute_provider_call,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fund(db_session, test_user, balance: int = 100) -> CreditAccount:
    """Create a credit account with given balance."""
    account = CreditAccount(
        user_id=test_user.id, plan_code="standard", monthly_grant=0,
        balance=balance, status="active",
    )
    db_session.add(account)
    await db_session.flush()
    return account


# ===================================================================
# Part A: Pre-flight Balance Check
# ===================================================================


class TestPreflightBalanceCheck:
    """Two-level balance gate in execute_provider_call."""

    @pytest.mark.anyio
    async def test_blocked_by_absolute_min(self, db_session, test_user):
        """Balance 0 < MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL=1 → blocked."""
        await _fund(db_session, test_user, balance=0)

        provider = MockProvider()
        request = ProviderRequest(feature="ocr")  # ocr min = 1

        with pytest.raises(InsufficientBalanceError) as exc_info:
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == "INSUFFICIENT_BALANCE"
        assert exc_info.value.required == 1  # max(1, 1) = 1
        assert exc_info.value.current == 0

    @pytest.mark.anyio
    async def test_blocked_by_feature_min(self, db_session, test_user):
        """Balance 1 meets absolute min but < image_edit feature min (5) → blocked."""
        await _fund(db_session, test_user, balance=1)

        provider = MockProvider()
        request = ProviderRequest(feature="image_edit")

        with pytest.raises(InsufficientBalanceError) as exc_info:
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == "INSUFFICIENT_BALANCE"
        assert exc_info.value.required == 5  # FEATURE_MIN_CREDITS["image_edit"]
        assert exc_info.value.current == 1

    @pytest.mark.anyio
    async def test_balance_above_min_allows_call(self, db_session, test_user):
        """Balance >= feature min → call proceeds normally."""
        await _fund(db_session, test_user, balance=100)

        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="test")

        result = await execute_provider_call(
            db=db_session, provider=provider, request=request,
            user_id=test_user.id, device_id=uuid.uuid4(),
        )
        assert result.provider == "mock"
        assert result.credits_charged > 0

    @pytest.mark.anyio
    async def test_user_id_none_skips_check(self, db_session):
        """user_id=None → no balance check, call proceeds."""
        provider = MockProvider()
        request = ProviderRequest(feature="mock_ad_copy", message="test")

        result = await execute_provider_call(
            db=db_session, provider=provider, request=request,
            user_id=None, device_id=None,
        )
        assert result.provider == "mock"
        assert result.credits_charged == 0  # skipped deduction

    @pytest.mark.anyio
    async def test_unknown_feature_uses_absolute_min(self, db_session, test_user):
        """Unknown feature → FEATURE_MIN_CREDITS default = absolute_min."""
        await _fund(db_session, test_user, balance=0)

        provider = MockProvider()
        request = ProviderRequest(feature="some_new_feature_xyz")

        with pytest.raises(InsufficientBalanceError) as exc_info:
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
            )
        assert exc_info.value.required == settings.MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL

    @pytest.mark.anyio
    async def test_insufficient_balance_logs_provider_call(self, db_session, test_user):
        """Blocked call writes provider_call_log with error_code=INSUFFICIENT_BALANCE."""
        await _fund(db_session, test_user, balance=0)

        provider = MockProvider()
        request = ProviderRequest(feature="ocr")
        rid = "req-balance-log-1"

        with pytest.raises(InsufficientBalanceError):
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
                request_id=rid,
            )

        stmt = select(ProviderCallLog).where(ProviderCallLog.request_id == rid)
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.status == "error"
        assert row.error_code == "INSUFFICIENT_BALANCE"
        assert row.credits_charged == 0

    @pytest.mark.anyio
    async def test_insufficient_balance_no_credit_ledger(self, db_session, test_user):
        """Blocked call does NOT touch credit_ledger."""
        await _fund(db_session, test_user, balance=0)

        count_before = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0

        provider = MockProvider()
        request = ProviderRequest(feature="ocr")

        with pytest.raises(InsufficientBalanceError):
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
            )

        count_after = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0
        assert count_after == count_before

    @pytest.mark.anyio
    async def test_balance_frozen_on_blocked_call(self, db_session, test_user):
        """Blocked call does not change credit account balance."""
        account = await _fund(db_session, test_user, balance=1)

        provider = MockProvider()
        request = ProviderRequest(feature="image_edit")  # min=5

        with pytest.raises(InsufficientBalanceError):
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
            )

        await db_session.refresh(account)
        assert account.balance == 1  # untouched


# ===================================================================
# Part B: Retry Logic
# ===================================================================


class TestRetryLogic:
    """Retry on transient errors, no retry on permanent errors."""

    def test_is_retryable_timeout(self):
        """TIMEOUT → retryable."""
        assert _is_retryable("TIMEOUT") is True

    def test_is_retryable_connection_error(self):
        """CONNECTION_ERROR → retryable."""
        assert _is_retryable("CONNECTION_ERROR") is True

    def test_is_retryable_api_error(self):
        """API_ERROR (5xx) → retryable."""
        assert _is_retryable("API_ERROR") is True

    def test_is_not_retryable_auth_error(self):
        """AUTH_ERROR → NOT retryable."""
        assert _is_retryable("AUTH_ERROR") is False

    def test_is_not_retryable_bad_request(self):
        """BAD_REQUEST → NOT retryable."""
        assert _is_retryable("BAD_REQUEST") is False

    def test_is_not_retryable_rate_limited(self):
        """RATE_LIMITED → NOT retryable."""
        assert _is_retryable("RATE_LIMITED") is False

    def test_is_not_retryable_none(self):
        """None → NOT retryable."""
        assert _is_retryable(None) is False

    @pytest.mark.anyio
    async def test_non_retryable_error_raised_immediately(self, db_session, test_user):
        """AUTH_ERROR → no retries, one error log."""
        await _fund(db_session, test_user, balance=100)

        provider = MockProvider()
        request = ProviderRequest(feature="test-error")  # MockProviderError(MOCK_ERROR)
        rid = "req-no-retry-1"

        # MOCK_ERROR is not in _RETRYABLE_ERROR_CODES
        assert not _is_retryable("MOCK_ERROR")

        with pytest.raises(MockProviderError):
            await execute_provider_call(
                db=db_session, provider=provider, request=request,
                user_id=test_user.id, device_id=uuid.uuid4(),
                request_id=rid,
            )

        # Only one log entry (no retry attempts)
        stmt = select(ProviderCallLog).where(ProviderCallLog.request_id == rid)
        rows = (await db_session.execute(stmt)).scalars().all()
        assert len(rows) == 1
        assert rows[0].status == "error"
        assert rows[0].error_code == "MOCK_ERROR"


# ===================================================================
# Part C: Fallback Chain
# ===================================================================


class TestFallbackChain:
    """Provider fallback when primary fails."""

    @pytest.mark.anyio
    async def test_fallback_rules_deepseek_to_mock(self):
        """FALLBACK_RULES maps deepseek → mock."""
        assert FALLBACK_RULES.get("deepseek") == "mock"
        assert FALLBACK_RULES.get("mock") is None  # mock has no fallback

    @pytest.mark.anyio
    async def test_primary_success_no_fallback(self, db_session):
        """When primary succeeds, fallback is never tried."""
        result = await route_and_execute_provider_call(
            db=db_session,
            feature="mock_ad_copy",
            plan="expert",  # → mock
            request=ProviderRequest(feature="mock_ad_copy", message="test"),
            user_id=None, device_id=None,
        )
        assert result.provider == "mock"
        # Only one provider_call_log entry (success, no error entries)
        count = await db_session.scalar(
            select(func.count()).select_from(ProviderCallLog)
        )
        assert count == 1

    @pytest.mark.anyio
    async def test_primary_fails_fallback_succeeds(self, db_session):
        """mock_ad_copy/standard → deepseek (fails*) → fallback mock (succeeds).

        *For this test we override the router so primary='mock',
        fallback='mock' doesn't make sense.  Instead we wire a
        custom registry with a failing primary and a working fallback.
        """
        # Build a custom registry: "bad" → fails, "good" → succeeds
        registry = ProviderRegistry()

        class FailingProvider(MockProvider):
            async def call(self, request):
                raise DeepSeekProviderError("TIMEOUT", "Simulated timeout")

        class GoodProvider(MockProvider):
            async def call(self, request):
                return await super().call(request)

        registry.register("bad", FailingProvider())
        registry.register("good", GoodProvider())

        # Router that resolves to "bad"
        rules = {"mock_ad_copy": {"standard": "bad"}}
        router = ProviderRouter(registry=registry, rules=rules)

        # Patch singletons
        import app.providers.router as _rmod
        import app.providers.registry as _regmod
        import app.services.provider_service as _psvc

        _old_router = _rmod._router
        _old_registry = _regmod._registry
        _old_fallback = dict(_psvc.FALLBACK_RULES)

        try:
            _rmod._router = router
            _regmod._registry = registry
            _psvc.FALLBACK_RULES["bad"] = "good"

            result = await route_and_execute_provider_call(
                db=db_session,
                feature="mock_ad_copy",
                plan="standard",
                request=ProviderRequest(feature="mock_ad_copy", message="test"),
                user_id=None, device_id=None,
            )
            # Should have fallen back to "good"
            assert result.provider == "mock"  # GoodProvider extends MockProvider
            assert result.model == "mock-text-v1"

            # Two log entries: error (bad) + success (good)
            error_count = await db_session.scalar(
                select(func.count()).select_from(ProviderCallLog).where(
                    ProviderCallLog.status == "error",
                )
            )
            success_count = await db_session.scalar(
                select(func.count()).select_from(ProviderCallLog).where(
                    ProviderCallLog.status == "success",
                )
            )
            assert error_count == 1
            assert success_count == 1
        finally:
            _rmod._router = _old_router
            _regmod._registry = _old_registry
            _psvc.FALLBACK_RULES.clear()
            _psvc.FALLBACK_RULES.update(_old_fallback)

    @pytest.mark.anyio
    async def test_insufficient_balance_no_fallback(self, db_session, test_user):
        """InsufficientBalanceError → propagate immediately, no fallback."""
        await _fund(db_session, test_user, balance=0)

        with pytest.raises(InsufficientBalanceError):
            await route_and_execute_provider_call(
                db=db_session,
                feature="mock_ad_copy",
                plan="standard",
                request=ProviderRequest(feature="mock_ad_copy", message="test"),
                user_id=test_user.id, device_id=uuid.uuid4(),
            )

    @pytest.mark.anyio
    async def test_all_providers_fail_raises_last_error(self, db_session):
        """When all providers in chain fail, the last error is raised."""
        registry = ProviderRegistry()

        class AlwaysFail(MockProvider):
            async def call(self, request):
                raise DeepSeekProviderError("API_ERROR", "boom")

        registry.register("fail1", AlwaysFail())
        registry.register("fail2", AlwaysFail())

        rules = {"mock_ad_copy": {"standard": "fail1"}}
        router = ProviderRouter(registry=registry, rules=rules)

        import app.providers.router as _rmod
        import app.providers.registry as _regmod
        import app.services.provider_service as _psvc

        _old_router = _rmod._router
        _old_registry = _regmod._registry
        _old_fallback = dict(_psvc.FALLBACK_RULES)

        try:
            _rmod._router = router
            _regmod._registry = registry
            _psvc.FALLBACK_RULES["fail1"] = "fail2"

            with pytest.raises(DeepSeekProviderError) as exc_info:
                await route_and_execute_provider_call(
                    db=db_session,
                    feature="mock_ad_copy",
                    plan="standard",
                    request=ProviderRequest(feature="mock_ad_copy", message="test"),
                    user_id=None, device_id=None,
                )
            # Last error (from fail2)
            assert exc_info.value.error_code == "API_ERROR"
        finally:
            _rmod._router = _old_router
            _regmod._registry = _old_registry
            _psvc.FALLBACK_RULES.clear()
            _psvc.FALLBACK_RULES.update(_old_fallback)


# ===================================================================
# Part D: Router Enhancements
# ===================================================================


class TestRouterEnhancements:
    """ProviderRouter.resolve_name + registry property."""

    def test_resolve_name_known_feature_plan(self):
        """resolve_name returns provider name string for known (feature, plan)."""
        router = get_provider_router()
        name = router.resolve_name("mock_ad_copy", "standard")
        assert name == "deepseek"  # DEFAULT_ROUTING_RULES
        assert isinstance(name, str)

    def test_resolve_name_expert_plan(self):
        """resolve_name for expert plan."""
        router = get_provider_router()
        name = router.resolve_name("mock_ad_copy", "expert")
        assert name == "mock"

    def test_resolve_name_unknown_feature_fallback(self):
        """Unknown feature → 'mock'."""
        router = get_provider_router()
        name = router.resolve_name("nonexistent_feature", "standard")
        assert name == "mock"

    def test_resolve_name_unknown_plan_fallback(self):
        """Unknown plan within known feature → 'mock'."""
        router = get_provider_router()
        name = router.resolve_name("mock_ad_copy", "free_tier")
        assert name == "mock"

    def test_registry_property_accessible(self):
        """router.registry provides access to the ProviderRegistry."""
        router = get_provider_router()
        registry = router.registry
        assert isinstance(registry, ProviderRegistry)
        assert "mock" in registry
        assert "deepseek" in registry


# ===================================================================
# Part E: API-level INSUFFICIENT_BALANCE (via mock_ai endpoint)
# ===================================================================


class TestApiInsufficientBalance:
    """API endpoint returns 402 for insufficient balance."""

    ENDPOINT = "/api/v1/mock-ai/ad-copy"

    VALID_BODY = {
        "product_name": "test product",
        "selling_points": ["fast", "cheap"],
        "platform": "douyin",
        "tone": "direct",
    }

    @pytest.fixture
    def _auth_header(self, test_user, test_device):
        from app.core.security import create_access_token
        token = create_access_token(
            sub=str(test_user.id),
            device_id=str(test_device.id),
            plan=test_user.plan_code,
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.anyio
    async def test_insufficient_balance_returns_402(
        self, client, db_session, test_user, test_device, _auth_header,
    ):
        """No credit account → balance=0 → 402 Payment Required."""
        # Ensure user has no credit account (balance=0)
        res = await client.post(
            self.ENDPOINT, json=self.VALID_BODY, headers=_auth_header,
        )
        assert res.status_code == 402, res.text
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INSUFFICIENT_BALANCE"
        assert "required" in body["error"].get("details", {})
        assert "current" in body["error"].get("details", {})

    @pytest.mark.anyio
    async def test_insufficient_balance_message_is_chinese(
        self, client, db_session, test_user, test_device, _auth_header,
    ):
        """Error message should be in Chinese."""
        res = await client.post(
            self.ENDPOINT, json=self.VALID_BODY, headers=_auth_header,
        )
        body = res.json()
        message = body["error"]["message"]
        assert "积分" in message
        assert "余额" in message

    @pytest.mark.anyio
    async def test_funded_user_returns_200(
        self, client, db_session, test_user, test_device, _auth_header,
    ):
        """User with enough credits → 200."""
        await _fund(db_session, test_user, balance=100)

        res = await client.post(
            self.ENDPOINT, json=self.VALID_BODY, headers=_auth_header,
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["data"]["credits_charged"] > 0
