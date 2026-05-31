# Module Context: Sprint-02 Task-04 Mock AI API Endpoint

## Status

`IMPLEMENTED` — implementation complete on branch `feature/sprint-02-task-04-mock-ai-api`. Awaiting Codex Review before commit and merge.

## Branch

- Implementation branch: `feature/sprint-02-task-04-mock-ai-api`

## Base

- Merge commit from PR #12: `c73f1c2` (`feat(provider): add mock provider foundation`)

## Implementation Evidence (2026-05-31)

- **Test results**:
  - Focused: `21 passed in 4.90s` (`pytest tests/test_mock_ai_api.py -v`)
  - Regression: `147 passed in 18.96s` (`pytest tests/ -v --ignore=tests/test_migrations_integration.py`)
- **Changed files**:
  - `cloud-backend/app/schemas/mock_ai.py` — 请求/响应 schema（Pydantic + field_validator）
  - `cloud-backend/app/api/v1/mock_ai.py` — 受保护 route handler
  - `cloud-backend/app/api/deps.py` — `mock_ad_copy` feature permission
  - `cloud-backend/app/main.py` — `request.state.request_id` + router
  - `cloud-backend/tests/test_mock_ai_api.py` — 21 个聚焦测试
  - `docs/05-api-contract.md`
  - `docs/23-mock-ai-api-endpoint.md`
  - `docs/module-context/sprint-02-task-04-mock-ai-api/context.md`
  - `tasks/current-task.md`
- **No DDL/dependency changes**: ✅
- **No real provider keys/SDKs/network calls**: ✅
- **No credit_ledger writes**: ✅
- **No modifications to provider/cost/provider_log/credit services**: ✅
- **No modifications to MockProvider**: ✅
- **Git diff --check**: passed

## Task Summary

Add one protected MVP endpoint:

```text
POST /api/v1/mock-ai/ad-copy
```

The endpoint calls `MockProvider` through `execute_provider_call`, returns deterministic mock ad copy, writes `provider_call_log`, and propagates `X-Request-ID` to both response and log.

## Key Behaviors

- Auth: requires Bearer token + active user + bound active device + valid plan + `mock_ad_copy` permission
- Provider: uses `MockProvider` via `execute_provider_call` — no real provider
- Request ID: middleware sets `request.state.request_id` from `X-Request-ID` header or auto-generates; route passes it to `execute_provider_call`
- Response: unified `{success, data, error, request_id}` wrapper; `data` includes feature/provider/model/text/estimated_cost/credits_charged
- No `raw_usage` exposed to client
- `credits_charged` = 0
- No `credit_ledger` writes
- Input validation: `product_name` (1–200 chars), `selling_points` (≤5 items, each ≤200 chars), `platform`/`tone` (1–50 chars)

## Allowed Files (this task)

- `cloud-backend/app/api/v1/mock_ai.py`
- `cloud-backend/app/api/deps.py`
- `cloud-backend/app/main.py`
- `cloud-backend/app/schemas/mock_ai.py`
- `cloud-backend/tests/test_mock_ai_api.py`
- `docs/05-api-contract.md`
- `docs/23-mock-ai-api-endpoint.md`
- `docs/module-context/sprint-02-task-04-mock-ai-api/context.md`
- `tasks/current-task.md`

## Forbidden Areas

- DDL and migrations
- Database models
- Provider base/mock implementation
- Provider, cost, provider-log, and credit services
- OpenAPI/shared DTO generated artifacts
- Frontend, desktop, official website, Tauri
- Real provider SDKs, API keys, secrets, environment variables
- Credit deduction, recharge, payment, order, grant, quota, expiration, admin workflows
- GitHub Actions workflows

## Residual Risks To Track

- This endpoint is intentionally mock-only and should not become the generic prompt API
- The response shape may be consumed by the future desktop MVP, so changes after merge should be treated as API contract changes
- Real credit deduction remains a separate approved task
- Real provider routing remains a separate approved task
- `provider_call_log` records `feature="mock_ad_copy"` with `message=""` — no raw user text logged; future prompt-bearing workflows must maintain this sanitization

## Review Checklist

- [x] Endpoint exists at `POST /api/v1/mock-ai/ad-copy`
- [x] Endpoint requires auth and active bound device
- [x] Endpoint uses backend feature permission `mock_ad_copy`
- [x] Request schema blocks client provider/model/cost/credit/user/device control
- [x] Endpoint calls `MockProvider` through `execute_provider_call`
- [x] Success writes one `provider_call_log` row
- [x] `X-Request-ID` is propagated to response and provider log
- [x] Response does not expose `raw_usage`
- [x] No raw product text, selling points, prompt, API key, token, or secret is logged
- [x] `credits_charged=0`
- [x] No `credit_ledger` write
- [x] No DDL/dependency/shared/frontend/desktop changes
