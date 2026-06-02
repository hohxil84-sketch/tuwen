"""S05-R05: Circuit breaker unit and integration tests.

Tests cover:
- State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
- before_call rejection when OPEN
- Cooldown expiry → HALF_OPEN
- HALF_OPEN success/failure behavior
- Registry singleton + status_all
- Admin health endpoint
"""

import time

import pytest

from app.providers.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker_registry,
)


# ---------------------------------------------------------------------------
# State machine — unit tests
# ---------------------------------------------------------------------------


class TestCircuitBreakerStateMachine:
    """Test the core CLOSED → OPEN → HALF_OPEN → CLOSED lifecycle."""

    def test_initial_state(self):
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"
        assert cb.consecutive_failures == 0
        assert cb.before_call() is True

    def test_closed_to_open(self):
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
        # 3 failures → OPEN
        for _ in range(3):
            assert cb.before_call() is True
            cb.on_failure()
        assert cb.state == "OPEN"
        assert cb.consecutive_failures == 3
        assert cb.opened_at is not None

    def test_open_rejects_calls(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
        cb.on_failure()
        cb.on_failure()
        assert cb.state == "OPEN"
        assert cb.before_call() is False

    def test_open_transitions_to_half_open_after_cooldown(self, monkeypatch):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

        # Trip the breaker
        cb.on_failure()
        cb.on_failure()
        assert cb.state == "OPEN"

        # Wait for cooldown
        time.sleep(0.15)

        # Next before_call should transition to HALF_OPEN and allow
        assert cb.before_call() is True
        assert cb.state == "HALF_OPEN"

    def test_half_open_success_resets_to_closed(self, monkeypatch):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

        # Trip → wait → HALF_OPEN
        cb.on_failure()
        cb.on_failure()
        time.sleep(0.15)
        assert cb.before_call() is True
        assert cb.state == "HALF_OPEN"

        # Success → CLOSED
        cb.on_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_failures == 0
        assert cb.opened_at is None

    def test_half_open_failure_goes_back_to_open(self, monkeypatch):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

        # Trip → wait → HALF_OPEN
        cb.on_failure()
        cb.on_failure()
        time.sleep(0.15)
        assert cb.before_call() is True
        assert cb.state == "HALF_OPEN"

        # Failure in HALF_OPEN → back to OPEN
        cb.on_failure()
        assert cb.state == "OPEN"

    def test_single_success_resets_counter(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.on_failure()
        cb.on_failure()
        assert cb.consecutive_failures == 2

        # One success resets everything
        cb.on_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_failures == 0

    def test_before_call_during_closed_returns_true(self):
        cb = CircuitBreaker()
        for _ in range(10):
            assert cb.before_call() is True
        assert cb.state == "CLOSED"

    def test_open_then_allow_after_long_cooldown(self, monkeypatch):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)

        # One failure trips it
        cb.on_failure()
        assert cb.state == "OPEN"

        # Still OPEN immediately
        assert cb.before_call() is False

        # Wait for cooldown
        time.sleep(0.1)

        # Now should be allowed
        assert cb.before_call() is True
        assert cb.state == "HALF_OPEN"


# ---------------------------------------------------------------------------
# CircuitBreakerOpenError
# ---------------------------------------------------------------------------


class TestCircuitBreakerOpenError:
    def test_error_message(self):
        exc = CircuitBreakerOpenError("deepseek")
        assert "OPEN" in str(exc)
        assert "deepseek" in str(exc)
        assert exc.provider_name == "deepseek"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestCircuitBreakerRegistry:
    def test_get_creates_default(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("deepseek")
        assert isinstance(cb, CircuitBreaker)
        assert cb.state == "CLOSED"

    def test_get_returns_same_instance(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get("deepseek")
        cb2 = reg.get("deepseek")
        assert cb1 is cb2

    def test_register_custom(self):
        reg = CircuitBreakerRegistry()
        custom = CircuitBreaker(failure_threshold=5, cooldown_seconds=120)
        reg.register("custom-provider", custom)
        assert reg.get("custom-provider") is custom

    def test_status_all(self):
        reg = CircuitBreakerRegistry()
        reg.get("deepseek").on_failure()
        reg.get("mock")

        status = reg.status_all()
        assert "deepseek" in status
        assert "mock" in status
        assert status["deepseek"]["consecutive_failures"] == 1
        assert status["deepseek"]["state"] == "CLOSED"
        assert status["mock"]["consecutive_failures"] == 0

    def test_get_or_none(self):
        reg = CircuitBreakerRegistry()
        assert reg.get_or_none("nonexistent") is None
        reg.get("deepseek")  # auto-creates
        assert isinstance(reg.get_or_none("deepseek"), CircuitBreaker)


# ---------------------------------------------------------------------------
# Admin health endpoint
# ---------------------------------------------------------------------------


class TestAdminProviderHealthEndpoint:
    async def _auth_headers(self, test_user, test_device, test_session):
        from app.core.security import create_access_token
        session, _plain = test_session
        token = create_access_token(
            sub=str(test_user.id),
            device_id=str(test_device.id),
            plan=test_user.plan_code,
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_admin_can_view_health(
        self, client, db_session, test_user, test_device, test_session,
    ):
        test_user.role = "admin"
        await db_session.flush()

        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/provider-health", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        providers = body["data"]["providers"]
        assert "deepseek" in providers
        assert "mock" in providers
        for p in providers.values():
            assert "state" in p
            assert p["state"] in ("CLOSED", "OPEN", "HALF_OPEN")
            assert "consecutive_failures" in p
            assert "opened_at" in p

    async def test_operator_can_view_health(
        self, client, db_session, test_user, test_device, test_session,
    ):
        test_user.role = "operator"
        await db_session.flush()

        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/provider-health", headers=headers)
        assert resp.status_code == 200, resp.text

    async def test_non_admin_gets_403(
        self, client, db_session, test_user, test_device, test_session,
    ):
        headers = await self._auth_headers(test_user, test_device, test_session)
        resp = await client.get("/api/v1/admin/provider-health", headers=headers)
        assert resp.status_code == 403
