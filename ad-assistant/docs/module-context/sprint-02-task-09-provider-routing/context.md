# Sprint-02 Task-09 Provider Routing Design — Module Context

## Status

`IMPLEMENTED_SELF_REVIEW_PASSED`

Branch: `feature/sprint-02-task-09-provider-routing`

## What was built

Provider routing layer that sits between route handlers and `execute_provider_call`:

```
Route Handler → ProviderRouter.route(feature, plan) → AsyncProvider
                   ↓
            ProviderRegistry.get(name) → MockProvider
                   ↓
            execute_provider_call(provider, ...) → ProviderResult
```

### New modules

| Module | Path | Purpose |
|--------|------|---------|
| `ProviderRegistry` | `app/providers/registry.py` | Named container of `AsyncProvider` instances |
| `ProviderRouter` | `app/providers/router.py` | (feature, plan) → provider selection |
| `route_and_execute_provider_call` | `app/services/provider_service.py` | High-level routing + execution entry point |

### Routing table

All (feature, plan) combinations resolve to `"mock"` via `DEFAULT_ROUTING_RULES`.
Unknown feature/plan falls back to `"mock"`.

### Key design decisions

- Router is **stateless** — routing table is a hardcoded dict
- Router's `route()` is **async** — forward-compatible with future async lookups
- `execute_provider_call()` is **unchanged** — still accepts explicit `provider`
- Registry uses **lazy singleton** — `MockProvider` registered on first access

### Testing

- 20 focused tests: registry (8), router (8), integration (4)
- 147 regression + 21 mock AI tests all pass

## Residual risks

- All routes currently resolve to MockProvider; real provider routing not yet tested
- No fallback/retry/circuit-breaker — would need future tasks
- Routing rules are hardcoded; future real providers may need DB-backed config

## Next steps

- When real providers are added, update `DEFAULT_ROUTING_RULES` to map appropriate features to real provider names
- Consider adding provider health checks and fallback chains
