# 23 Mock AI API Endpoint

## Purpose

This document defines Sprint-02 Task-04: Mock AI API Endpoint.

The goal is to expose one protected backend endpoint that calls the already-merged `MockProvider` path. This gives the future desktop MVP a real cloud-backend target without introducing real AI providers, billing deduction, or frontend/desktop code.

## Endpoint

```text
POST /api/v1/mock-ai/ad-copy
```

The endpoint is mock-only. It generates deterministic mock ad copy and writes a provider call log.

## Request

Recommended request body:

```json
{
  "product_name": "A4 poster printing",
  "selling_points": ["same-day pickup", "waterproof material"],
  "platform": "douyin",
  "tone": "direct"
}
```

Rules:

- `product_name` must be non-empty and bounded.
- `selling_points` must be bounded in item count and item length.
- `platform` and `tone` must be bounded strings.
- The client must not submit provider, model, raw cost, estimated cost, credits charged, user ID, device ID, request ID, or permission decisions.

## Response

Recommended `data` shape:

```json
{
  "feature": "mock_ad_copy",
  "provider": "mock",
  "model": "mock-text-v1",
  "text": "Mock generated text ...",
  "estimated_cost": 0.0,
  "credits_charged": 0
}
```

The response must use the existing unified wrapper:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "req_xxx"
}
```

Do not expose `raw_usage` to normal clients.

## Auth And Device Requirements

The endpoint must require:

- valid access token;
- active user;
- bound active device;
- valid plan;
- feature permission for `mock_ad_copy`.

For Task-04, `mock_ad_copy` may be allowed for:

- `standard`
- `expert`
- `enterprise`

Unknown features must remain denied by default.

## Provider Logging

Successful calls must write `provider_call_log` through the existing provider service path.

Required provider log fields:

- authenticated `user_id`;
- authenticated `device_id`;
- request ID;
- feature `mock_ad_copy`;
- provider `mock`;
- model `mock-text-v1`;
- status `success`;
- backend-computed estimated cost;
- `credits_charged=0`;
- latency if available.

If `X-Request-ID` is supplied, the same request ID must appear in both the API response and `provider_call_log.request_id`.

## Credit Rules

Task-04 does not implement real billing.

Rules:

- `credits_charged` remains `0`.
- No `credit_ledger` row is created.
- No account balance is changed.
- Clients cannot submit any final credit or cost decision.

## Security Rules

Do not:

- log raw product text or selling points;
- log raw prompts;
- expose `raw_usage`;
- add provider keys, secrets, SDKs, or environment variables;
- call external AI providers;
- create a generic arbitrary prompt endpoint.

The route should produce a narrow internal provider request for `MockProvider` only.

## Test Expectations

Required focused command:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_mock_ai_api.py -v
```

Required backend regression command:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

Whitespace check:

```bash
cd D:/Project/ad-assistant
git diff --check
```

PostgreSQL migration integration tests are not required because no DDL changes are allowed.

## Non-Goals

- Real provider integration.
- Provider routing.
- Credit deduction.
- DDL or migration changes.
- OpenAPI/shared DTO generated artifact updates.
- Desktop or frontend UI.
- Payment, recharge, orders, grants, admin, quotas, expiration.
- Queues, background jobs, retries, rate limiting infrastructure.

## Implementation Evidence (2026-05-31)

- **Implementation branch**: `feature/sprint-02-task-04-mock-ai-api`
- **Head commit**: `(pending — awaiting Codex review)`
- **Endpoint**: `POST /api/v1/mock-ai/ad-copy`
- **Changed files**:
  - `cloud-backend/app/schemas/mock_ai.py` — 请求/响应 schema（含 selling_points 逐项长度校验）
  - `cloud-backend/app/api/v1/mock_ai.py` — 受保护 route handler
  - `cloud-backend/app/api/deps.py` — 新增 `mock_ad_copy` 到 FEATURE_PLAN_REQUIREMENTS
  - `cloud-backend/app/main.py` — `request.state.request_id` 注入 + router 注册
  - `cloud-backend/tests/test_mock_ai_api.py` — 21 个聚焦测试
  - `docs/05-api-contract.md`
  - `docs/23-mock-ai-api-endpoint.md`
  - `docs/module-context/sprint-02-task-04-mock-ai-api/context.md`
  - `tasks/current-task.md`
- **Test results**:
  - Focused: `21 passed` (`pytest tests/test_mock_ai_api.py -v`)
  - Regression: `147 passed` (`pytest tests/ -v --ignore=tests/test_migrations_integration.py`)
- **No DDL/dependency/shared/frontend/desktop changes**: ✅ confirmed
- **No real provider keys/SDKs/network calls**: ✅ confirmed
- **No credit_ledger writes**: ✅ confirmed
- **request_id propagation**: ✅ confirmed (X-Request-ID → response + provider_call_log)
- **raw_usage not exposed**: ✅ confirmed

## Review Gate

After CC implementation, Codex should review before commit approval.

Review focus:

- API contract and response wrapper;
- auth/device enforcement;
- request ID propagation;
- provider log correctness;
- no sensitive logging;
- no credit ledger writes;
- no real provider/dependency/secrets;
- focused API tests and backend regression results.
