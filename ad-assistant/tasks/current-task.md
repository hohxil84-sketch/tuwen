# Current Task: Sprint-03 Task-02 First Real Provider Integration (DeepSeek)

## Status

`MVP_REQUIRED`

## Background

Sprint-02 built the full Provider abstraction stack — `AsyncProvider` interface, `MockProvider`, `ProviderRegistry`, `ProviderRouter`, and `route_and_execute_provider_call()`. All routes currently resolve to `MockProvider`. Sprint-03 Task-02 adds the first real AI Provider so that `mock_ad_copy` + `standard` plan users get actual AI-generated ad copy.

## Goal

Integrate DeepSeek Chat API as the first real `AsyncProvider` implementation behind the existing routing layer.

## What To Build

### 1. New dependency: `openai` SDK
- Add `openai>=1.0.0` to `cloud-backend/pyproject.toml`
- DeepSeek API is OpenAI-compatible; use the `openai` SDK with custom `base_url`

### 2. `DeepSeekProvider` (new file)
- `cloud-backend/app/providers/deepseek_provider.py`
- Implements `AsyncProvider.call()` → `ProviderResult`
- Uses `openai.AsyncOpenAI` client
- Maps DeepSeek response: `choices[0].message.content` → `result.text`, `usage.prompt_tokens` → `input_units`, `usage.completion_tokens` → `output_units`
- `raw_usage` contains only: model, finish_reason, usage token counts (NOT raw prompt)
- Error handling: auth failure (401), rate limit (429), timeout, connection error → descriptive exceptions
- API key read from `settings.DEEPSEEK_API_KEY` at call time (not stored as instance field beyond client init)

### 3. Configuration
- `cloud-backend/app/core/config.py`: add `DEEPSEEK_API_KEY: str = ""`, `DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"`, `DEEPSEEK_MODEL: str = "deepseek-chat"`
- API key has no default — if empty, `DeepSeekProvider.call()` raises a clear error

### 4. Registry registration
- `cloud-backend/app/providers/registry.py`: register `"deepseek"` → `DeepSeekProvider()`

### 5. Routing rules
- `cloud-backend/app/providers/router.py`: `mock_ad_copy` / `standard` → `"deepseek"`
- All other routes unchanged (still `"mock"`)
- Routing table structure is dict-of-dicts — extensible by design; only one entry changes

### 6. Cost service — real DeepSeek pricing
- `cloud-backend/app/services/cost_service.py`: add `calculate_deepseek_cost(input_units, output_units)` using official pricing (¥1/1M input, ¥2/1M output)
- Keep `calculate_mock_cost()` unchanged

### 7. Provider service — dispatch cost by provider name
- `cloud-backend/app/services/provider_service.py`: in `execute_provider_call()`, after `provider.call()`, check `result.provider` and dispatch:
  - `"deepseek"` → `calculate_deepseek_cost()`
  - `"mock"` (or unknown) → `calculate_mock_cost()`
- Also fix hardcoded `"mock"` / `"mock-text-v1"` in error handlers — use `result.provider` / `result.model` when available, fall back to generic values for unknown exceptions

### 8. Mock AI endpoint — pass real prompt
- `cloud-backend/app/api/v1/mock_ai.py`: construct human-readable prompt from `MockAdCopyRequest` fields and pass via `ProviderRequest.message`
- Prompt text goes through `provider.call()` but is NOT recorded in `provider_call_log` or `raw_usage` (provider_service only logs metadata)

### 9. Tests
- `cloud-backend/tests/test_deepseek_provider.py`: focused tests
- Mock `openai.AsyncOpenAI` to avoid real network calls
- Cover: success path, auth error, rate limit, timeout, empty API key, model mapping, cost calculation
- Verify `raw_usage` does not contain prompt text

### 10. Docs
- `docs/06-provider-architecture.md`: add DeepSeekProvider section
- `docs/sprint-02-summary.md`: update safety boundaries note
- `PROGRESS.md`: add S03-T02 entry

## What Not To Build

- No credit deduction (S03-T03)
- No fallback/retry/circuit-breaker (future task)
- No other features or plans routed to DeepSeek
- No client-side changes (desktop, Tauri, website)
- No DDL changes
- No API contract changes (shared DTO, OpenAPI)
- No other providers (OpenAI, Claude — future tasks)
- No removal of MockProvider

## Allowed Files

### Backend
- `cloud-backend/pyproject.toml`
- `cloud-backend/app/core/config.py`
- `cloud-backend/app/providers/__init__.py`
- `cloud-backend/app/providers/base.py` (if ProviderRequest/ProviderResult need adjustment)
- `cloud-backend/app/providers/deepseek_provider.py` (NEW)
- `cloud-backend/app/providers/registry.py`
- `cloud-backend/app/providers/router.py`
- `cloud-backend/app/services/cost_service.py`
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/app/api/v1/mock_ai.py`
- `cloud-backend/tests/test_deepseek_provider.py` (NEW)

### Docs
- `docs/06-provider-architecture.md`
- `docs/sprint-02-summary.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- All other files (desktop, shared, Tauri, website, CI, DDL, auth, credit, etc.)

## Acceptance Criteria

1. `DeepSeekProvider` implements `AsyncProvider` and returns valid `ProviderResult`
2. `mock_ad_copy` + `standard` routes to `"deepseek"`; all other routes unchanged
3. Cost dispatch works: deepseek → `calculate_deepseek_cost()`, mock → `calculate_mock_cost()`
4. API key missing → clear error; auth failure (401) → clear error; rate limit (429) → clear error
5. `raw_usage` does not contain prompt text
6. `provider_call_log` does not contain prompt text
7. Backend tests all pass (existing 167 + new deepseek tests)
8. `git diff --check` passes

## Test Method

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_deepseek_provider.py -v
python -m pytest tests/ -v
cd D:/Project/ad-assistant
git diff --check
```

## Dependency Permission

**Yes** — add `openai>=1.0.0` to `pyproject.toml`. No other new dependencies.

## Major Change Status

**Yes** — touches Provider interface (first real implementation), real AI Provider calls, and new dependency. User confirmed all three on 2026-06-01.

## Security Requirements

- API key from `Settings().DEEPSEEK_API_KEY`, never hardcoded
- `raw_usage` excludes raw prompt text, API key, secrets
- `provider_call_log` excludes raw prompt text
- No API key sent to client
- Client does not call DeepSeek directly

## Rollback Plan

- Revert routing rule: `mock_ad_copy/standard` back to `"mock"`
- Or remove `"deepseek"` from registry → `ProviderNotFoundError` → falls back to mock
- Remove `openai` dependency from `pyproject.toml`

## Completion Output Required

- Modified files list
- Implemented / not implemented
- Self-review checklist
- Test commands and results
- Risk assessment
