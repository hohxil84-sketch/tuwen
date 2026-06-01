# AI Provider layer package
# ALL AI model calls MUST go through this layer.
#
# Sprint-02 Task-03: base interface + MockProvider implemented
# Sprint-02 Task-09: ProviderRegistry + ProviderRouter added
# Sprint-03 Task-02: DeepSeekProvider (first real provider) added
#
# Architecture:
#   Route Handler → ProviderRouter.route(feature, plan) → AsyncProvider
#                      ↓
#               ProviderRegistry.get(name) → DeepSeekProvider / MockProvider
#
# Modules:
# - base.py                  (AsyncProvider interface, ProviderRequest, ProviderResult)
# - mock_provider.py         (deterministic mock for testing/dev)
# - deepseek_provider.py     (real AI — DeepSeek Chat API via openai SDK)
# - registry.py              (ProviderRegistry — named container)
# - router.py                (ProviderRouter — feature/plan → provider selection)
