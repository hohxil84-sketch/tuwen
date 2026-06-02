"""Circuit breaker for Provider reliability (S05-R05).

Per-provider in-memory circuit breaker with three states:

- **CLOSED** — normal operation, calls pass through
- **OPEN** — tripped after ``failure_threshold`` consecutive failures;
  calls are rejected immediately (fast-fail) for ``cooldown_seconds``
- **HALF_OPEN** — after cooldown expires, a single probe call is allowed;
  success → CLOSED, failure → OPEN again
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        super().__init__(
            f"Circuit breaker is OPEN for provider '{provider_name}'"
        )


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------


@dataclass
class CircuitBreaker:
    """Per-provider circuit breaker.

    Args:
        failure_threshold: Consecutive failures before tripping to OPEN.
        cooldown_seconds: Seconds to stay OPEN before transitioning to HALF_OPEN.

    Usage::

        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)

        if not cb.before_call():
            raise CircuitBreakerOpenError("deepseek")

        try:
            result = await provider.call(request)
            cb.on_success()
        except Exception:
            cb.on_failure()
            raise
    """

    failure_threshold: int = 3
    cooldown_seconds: float = 60.0

    # Internal state
    _state: CircuitState = CircuitState.CLOSED
    _consecutive_failures: int = 0
    _opened_at: float | None = None

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state.value

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    @property
    def opened_at(self) -> float | None:
        return self._opened_at

    def status(self) -> dict[str, Any]:
        """Return a JSON-safe status dict for the health-check endpoint."""
        return {
            "state": self.state,
            "consecutive_failures": self._consecutive_failures,
            "opened_at": self._opened_at,
        }

    # ------------------------------------------------------------------
    # state machine
    # ------------------------------------------------------------------

    def before_call(self) -> bool:
        """Check whether a call is allowed.  Must be called **before** each
        provider invocation.

        Returns:
            True if the call may proceed; False if the circuit is OPEN and
            should be fast-failed.
        """
        now = time.monotonic()

        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if self._opened_at is not None and (
                now - self._opened_at >= self.cooldown_seconds
            ):
                # Cooldown expired → allow one probe
                self._state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN — allow exactly one call
        return True

    def on_success(self) -> None:
        """Report a **successful** provider call."""
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = None

    def on_failure(self) -> None:
        """Report a **failed** provider call."""
        self._consecutive_failures += 1

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN trips back to OPEN immediately
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()
        elif self._consecutive_failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()


# ---------------------------------------------------------------------------
# Registry — one breaker per registered provider name
# ---------------------------------------------------------------------------


class CircuitBreakerRegistry:
    """Map provider name → ``CircuitBreaker`` instance.

    Usage::

        reg = CircuitBreakerRegistry()
        reg.register("deepseek", CircuitBreaker(failure_threshold=3))
        cb = reg.get("deepseek")
    """

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def register(self, name: str, breaker: CircuitBreaker) -> None:
        self._breakers[name] = breaker

    def get(self, name: str) -> CircuitBreaker:
        """Return the breaker for *name*, creating a default one if absent."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker()
        return self._breakers[name]

    def get_or_none(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def status_all(self) -> dict[str, dict[str, Any]]:
        """Return {provider_name: status_dict} for the health-check endpoint."""
        return {name: cb.status() for name, cb in self._breakers.items()}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_cb_registry: CircuitBreakerRegistry | None = None


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Return the module-level ``CircuitBreakerRegistry`` singleton."""
    global _cb_registry
    if _cb_registry is None:
        _cb_registry = CircuitBreakerRegistry()
        # Pre-register breakers for known providers
        _cb_registry.register("deepseek", CircuitBreaker(failure_threshold=3, cooldown_seconds=60))
        _cb_registry.register("mock", CircuitBreaker(failure_threshold=3, cooldown_seconds=60))
    return _cb_registry
