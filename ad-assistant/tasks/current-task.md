# Current Task: Sprint-02 Task-09 Provider Routing Design

## Status

`IMPLEMENTED_SELF_REVIEW_PASSED`

Implemented by Claude Code on 2026-06-01. Self-review passed. Awaiting commit + push + PR.

## Implementation Evidence

- **Branch**: `feature/sprint-02-task-09-provider-routing`
- **Registry**: `ProviderRegistry` with singleton, pre-loaded with `MockProvider` as `"mock"`
- **Router**: `ProviderRouter` with `DEFAULT_ROUTING_RULES`, all routes → `"mock"`
- **Service**: `route_and_execute_provider_call()` as high-level entry point
- **Endpoint**: `mock_ai.py` no longer imports `MockProvider` directly
- **Tests**: 167 total passed (147 regression + 21 mock AI + 20 routing)
- **`git diff --check`**: ✅
- **OpenAPI gen**: unchanged ✅
- **No real provider SDKs/keys/network calls**: ✅
- **Wire response unchanged**: ✅

## Background

The current provider execution path is hardwired: every endpoint instantiates a specific `AsyncProvider` and passes it to `execute_provider_call()`. In `mock_ai.py`:

```python
provider = MockProvider()
result = await execute_provider_call(db=db, provider=provider, ...)
```

This works for a single mock provider but cannot support multiple providers, plan-based routing, or feature-based routing.

We need a provider routing layer between the route handler and `execute_provider_call()`. The router selects which provider to use based on feature + plan.

**Important**: This task builds the routing infrastructure. No real provider implementations (no SDKs, no API keys, no network calls). All routes still resolve to `MockProvider` — but through the router.

## Goal

1. **Provider Registry** — named container of available providers
2. **Provider Router** — selects provider based on (feature, plan)
3. **Update execution path** — endpoints call router instead of instantiating providers directly
4. **Update existing endpoint** — `mock_ai.py` uses routing

## What To Build

### 1. Provider Registry (`app/providers/registry.py`)

- `ProviderRegistry` class: `register(name, provider)`, `get(name)`, `list_names()`, `__contains__`
- Module-level singleton `get_provider_registry()` pre-registered with `MockProvider` as `"mock"`

### 2. Provider Router (`app/providers/router.py`)

- `ProviderRouter` class: `route(feature, plan) -> AsyncProvider`
- Routing rules: dict mapping `(feature, plan)` → `provider_name`
- All routes resolve to `"mock"` for now; unknown feature/plan falls back to `"mock"`
- `ProviderNotFoundError` for lookup failures
- Module-level singleton `get_provider_router()`

### 3. Update `provider_service.py`

- Add `route_and_execute_provider_call()` — routes then executes
- Existing `execute_provider_call()` unchanged

### 4. Update `mock_ai.py`

- Remove `MockProvider` import
- Use `route_and_execute_provider_call()` instead of direct instantiation

### 5. Tests (`tests/test_provider_routing.py`)

- Registry unit tests, router unit tests, integration test

### 6. Documentation

- `docs/06-provider-architecture.md`, `docs/sprint-02-summary.md`, `PROGRESS.md`, module context

## What Not To Build

- No real providers (DeepSeek, OpenAI, Claude, etc.)
- No AI SDK, API key, environment variable, or network call
- No credit deduction or billing
- No provider fallback/retry chains (future task)
- No database tables for routing rules
- No modification to `ProviderRequest`, `ProviderResult`, or `AsyncProvider`
- No new API endpoints; no changes to endpoints other than `mock_ai.py`
- No new dependencies; no DDL, auth, credit, device, or shared contract changes

## Allowed Files

- `cloud-backend/app/providers/__init__.py`
- `cloud-backend/app/providers/registry.py` — new
- `cloud-backend/app/providers/router.py` — new
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/app/api/v1/mock_ai.py`
- `cloud-backend/tests/test_provider_routing.py` — new
- `docs/06-provider-architecture.md`
- `docs/sprint-02-summary.md`
- `tasks/current-task.md`
- `PROGRESS.md`
- `docs/module-context/sprint-02-task-09-provider-routing/context.md` — new

## Forbidden Files

- `cloud-backend/app/providers/base.py`, `mock_provider.py`
- `cloud-backend/app/schemas/**`, `models/**`, `core/**`
- `cloud-backend/app/services/cost_service.py`
- `cloud-backend/app/api/v1/auth.py`, `credits.py`, `devices.py`, `usage.py`, `provider_log.py`
- `cloud-backend/tests/test_mock_ai_api.py`
- `shared/**`, `desktop-app/**`, `migrations/**`, `.github/workflows/**`
- dependency files, `.env` files

## Acceptance Criteria

1. `ProviderRegistry` exists with register/get/list_names/contains, pre-loaded with `MockProvider` as `"mock"`
2. `ProviderRouter` routes (feature, plan) → provider, falls back to `"mock"` for unknown
3. `route_and_execute_provider_call()` works end-to-end
4. `mock_ai.py` no longer imports `MockProvider` directly
5. New routing tests pass; 147 regression + 21 mock AI tests pass
6. `git diff --check` passes; wire response unchanged
7. No real provider SDKs, API keys, or network calls

## Major Change Status

**Yes** — touches Provider interface call path (CODEX.md high-risk boundary). User confirmed 2026-06-01.

## Suggested Branch

`feature/sprint-02-task-09-provider-routing`
