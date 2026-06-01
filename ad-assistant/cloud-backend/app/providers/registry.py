"""Provider Registry — named container of AsyncProvider instances.

Sprint-02 Task-09: first routing infrastructure module.

Provides a thread-safe, lazy-initialised singleton that holds all
available :class:`AsyncProvider` instances by name.
"""

from __future__ import annotations

from app.providers.base import AsyncProvider


class ProviderRegistryError(Exception):
    """Raised when a registry operation fails (e.g. duplicate name, name not found)."""


class ProviderRegistry:
    """Thread-safe registry of named :class:`AsyncProvider` instances.

    Usage::

        registry = ProviderRegistry()
        registry.register("mock", MockProvider())
        provider = registry.get("mock")
    """

    def __init__(self) -> None:
        self._providers: dict[str, AsyncProvider] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def register(self, name: str, provider: AsyncProvider) -> None:
        """Register a provider instance under *name*.

        Raises:
            ProviderRegistryError: if *name* is already registered.
        """
        if name in self._providers:
            raise ProviderRegistryError(
                f"Provider '{name}' is already registered"
            )
        self._providers[name] = provider

    def get(self, name: str) -> AsyncProvider:
        """Return the provider registered under *name*.

        Raises:
            ProviderRegistryError: if *name* is not registered.
        """
        if name not in self._providers:
            raise ProviderRegistryError(
                f"Provider '{name}' is not registered. "
                f"Available: {sorted(self._providers.keys())}"
            )
        return self._providers[name]

    def list_names(self) -> list[str]:
        """Return a sorted list of all registered provider names."""
        return sorted(self._providers.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._providers


# ---------------------------------------------------------------------------
# module-level singleton
# ---------------------------------------------------------------------------

_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Return the module-level :class:`ProviderRegistry` singleton.

    On first call the registry is populated with ``MockProvider``
    (registered as ``"mock"``).
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        # Lazy import to avoid circular imports
        from app.providers.mock_provider import MockProvider  # noqa: PLC0415

        _registry.register("mock", MockProvider())
    return _registry
