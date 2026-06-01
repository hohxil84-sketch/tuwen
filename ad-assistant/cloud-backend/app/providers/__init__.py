# AI Provider layer package
# ALL AI model calls MUST go through this layer.
#
# Sprint-02 Task-03: base interface + MockProvider implemented
# Sprint-02 Task-09: ProviderRegistry + ProviderRouter added
#
# Architecture:
#   Route Handler → ProviderRouter.route(feature, plan) → AsyncProvider
#                      ↓
#               ProviderRegistry.get(name) → MockProvider (or future real provider)
#
# Modules:
# - base.py               (AsyncProvider interface, ProviderRequest, ProviderResult)
# - mock_provider.py      (deterministic mock for testing/dev)
# - registry.py           (ProviderRegistry — named container)
# - router.py             (ProviderRouter — feature/plan → provider selection)
