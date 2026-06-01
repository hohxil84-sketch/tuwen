"""Provider Router — selects an AsyncProvider based on (feature, plan).

Sprint-02 Task-09: first routing infrastructure module.

All routes currently resolve to ``"mock"``.  The routing table is designed
to accept real provider names as soon as those providers are implemented
and registered.
"""

from __future__ import annotations

from app.providers.base import AsyncProvider
from app.providers.registry import ProviderRegistry, get_provider_registry


class ProviderNotFoundError(Exception):
    """Raised when no provider can be resolved for a given (feature, plan)."""


# ---------------------------------------------------------------------------
# default routing table
# ---------------------------------------------------------------------------
#
# Shape: {feature: {plan: provider_name}}
#
# Unknown features and unknown plans both fall back to "mock".
# When real providers are added, update this table to route appropriate
# (feature, plan) combinations to real provider names.

DEFAULT_ROUTING_RULES: dict[str, dict[str, str]] = {
    "mock_ad_copy": {
        "standard": "deepseek",
        "expert": "mock",
        "enterprise": "mock",
    },
    "ocr": {
        "standard": "mock",
        "expert": "mock",
        "enterprise": "mock",
    },
    "text_gen": {
        "standard": "mock",
        "expert": "mock",
        "enterprise": "mock",
    },
    "image_edit": {
        "standard": "mock",
        "expert": "mock",
        "enterprise": "mock",
    },
}

# ---------------------------------------------------------------------------
# router
# ---------------------------------------------------------------------------


class ProviderRouter:
    """Select an :class:`AsyncProvider` from a :class:`ProviderRegistry`
    based on feature and plan.

    Usage::

        router = ProviderRouter(registry=get_provider_registry())
        provider = await router.route("mock_ad_copy", "standard")
    """

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        rules: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self._registry = registry or get_provider_registry()
        self._rules = rules or DEFAULT_ROUTING_RULES

    def resolve_name(self, feature: str, plan: str) -> str:
        """Resolve *(feature, plan)* to a provider **name** string.

        This is the pure name-resolution half of :meth:`route`.  Callers
        that need to build fallback chains can use this to learn the
        primary provider name without obtaining the instance yet.

        Returns:
            str: provider name (never ``None`` — unknown combinations
            fall back to ``"mock"``).
        """
        provider_name = (
            self._rules.get(feature, {}).get(plan)
            or self._rules.get(feature, {}).get("default")
        )
        if provider_name is None:
            provider_name = "mock"
        return provider_name

    async def route(self, feature: str, plan: str) -> AsyncProvider:
        """Resolve *(feature, plan)* to a concrete provider instance.

        Returns:
            An :class:`AsyncProvider` instance from the registry.

        Raises:
            ProviderNotFoundError: if the resolved name is not registered.
        """
        provider_name = self.resolve_name(feature, plan)

        if provider_name not in self._registry:
            raise ProviderNotFoundError(
                f"No provider registered for feature='{feature}' "
                f"plan='{plan}' (resolved to '{provider_name}', "
                f"which is not in the registry). "
                f"Available: {self._registry.list_names()}"
            )

        return self._registry.get(provider_name)

    @property
    def registry(self) -> ProviderRegistry:
        """Expose the underlying :class:`ProviderRegistry` for fallback logic."""
        return self._registry


# ---------------------------------------------------------------------------
# module-level singleton
# ---------------------------------------------------------------------------

_router: ProviderRouter | None = None


def get_provider_router() -> ProviderRouter:
    """Return the module-level :class:`ProviderRouter` singleton."""
    global _router
    if _router is None:
        _router = ProviderRouter(
            registry=get_provider_registry(),
            rules=DEFAULT_ROUTING_RULES,
        )
    return _router
