# Current Task: Sprint-02 Task-04 Mock AI API Endpoint

## Status

`IMPLEMENTED` — implementation complete on branch `feature/sprint-02-task-04-mock-ai-api`. 21 focused tests pass, 147 regression pass. Awaiting Codex Review before commit and merge.

Codex prepared this task sheet after PR #12 was merged to `main`.

Implementation completed by CC on 2026-05-31.

## Suggested Branch

`feature/sprint-02-task-04-mock-ai-api`, based on latest `main`.

If a local Git ref permission or slash-name issue occurs, use the flat branch name `sprint-02-task-04-mock-ai-api`.

## Prerequisites

- Sprint-02 Task-03 Provider Mock Foundation was merged to `main` by PR #12.
- Latest verified merge commit: `c73f1c2` (`feat(provider): add mock provider foundation`).
- Provider mock foundation commit: `34b1528`.
- Provider mock focused tests passed during review: `24 passed, 1 warning`.
- Backend regression tests passed during review: `126 passed, 1 warning`.
- PR #12 GitHub check `pg-integration` passed.
- `MockProvider`, `ProviderRequest`, `ProviderResult`, `calculate_mock_cost`, and `execute_provider_call` now exist.
- Existing API style uses `/api/v1/*`, `success_response`, auth/device dependencies, schemas, service layer, and focused API tests.

## Background

The backend now has an internal mock provider path, but no public feature endpoint calls it yet. The next step is a minimal authenticated API endpoint that proves a desktop or frontend client can call the cloud backend and receive a mock AI result while the backend logs the provider call.

This is the first intentionally client-callable mock AI feature. It must be small, protected, and clearly marked as mock-only.

## Major Change Proposal

This task modifies the API contract by adding one new endpoint. User confirmation is required before implementation.

1. Reason
   - Turn the internal mock provider foundation into a callable backend MVP path.
   - Let the future desktop MVP call a real backend endpoint instead of fake local data.
   - Prove auth/device checks, request validation, provider execution, and provider logging work together.

2. Risks
   - Public API shape may become a contract used by the desktop app.
   - Prompt-like user input could accidentally be logged if route/service boundaries are careless.
   - Missing auth/device checks would expose mock AI execution to unauthenticated clients.
   - Request ID may diverge between API response and provider log if not propagated deliberately.

3. Impact
   - Adds one POST endpoint under `/api/v1`.
   - Adds request/response schemas and API tests.
   - Updates API docs for the new endpoint.
   - No database schema change.
   - No real AI provider, no billing deduction, no desktop UI yet.

4. Rollback
   - Remove the new route and schema files.
   - Remove the route registration from `app/main.py`.
   - Remove focused API tests and docs for this endpoint.
   - No database rollback is needed.

5. Backward Compatibility
   - Compatible. Existing endpoints remain unchanged.
   - The new endpoint is additive.

6. Database Migration
   - None. This task must not add, remove, or edit DDL files.

## What To Build

### 1. Add a protected mock AI endpoint

Add a new endpoint:

```text
POST /api/v1/mock-ai/ad-copy
```

Purpose:

- Generate deterministic mock ad copy through `MockProvider`.
- Return a unified API response.
- Write `provider_call_log`.
- Provide a backend target for the future Desktop MVP task.

Required behavior:

- Must require valid auth token and bound active device using existing dependencies.
- Must call `verify_plan(user)`.
- Must call `verify_feature(user, "mock_ad_copy")` or an equivalent route-level feature check.
- Must instantiate/use `MockProvider`.
- Must call `execute_provider_call`.
- Must pass the authenticated `user_id`, authenticated `device_id`, feature name, and request ID into provider logging.
- Must return `success_response(...)`.
- Must not expose raw `raw_usage` to normal clients.
- Must not return or accept provider cost, final credit charge, plan decision, or provider selection from the client.

Recommended request body:

```json
{
  "product_name": "string",
  "selling_points": ["string"],
  "platform": "douyin",
  "tone": "direct"
}
```

Recommended response `data`:

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

The response body wrapper remains:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "req_xxx"
}
```

### 2. Add schemas

Add:

- `cloud-backend/app/schemas/mock_ai.py`

Required schema behavior:

- Validate `product_name` is non-empty and reasonably bounded.
- Validate `selling_points` length and item length are bounded.
- Validate `platform` and `tone` are bounded strings.
- Do not include client-submitted provider, model, cost, credits, plan, user_id, device_id, or request_id in the request schema.
- Response schema may include provider/model/estimated_cost/credits_charged because those values are computed by the backend.

### 3. Add route module

Add:

- `cloud-backend/app/api/v1/mock_ai.py`

Required route behavior:

- Use existing dependency pattern from `app/api/v1/provider_log.py`.
- Use `get_current_user_with_device`.
- Use `get_db`.
- Use `success_response`.
- Use `MockProvider` and `execute_provider_call`.
- Convert `MockProviderError` to a sanitized HTTP error if needed.
- Do not log raw user text.
- Do not expose `raw_usage`.

### 4. Register route and feature permission

Update:

- `cloud-backend/app/main.py`
- `cloud-backend/app/api/deps.py`

Required behavior:

- Include the new router in `app/main.py`.
- Add a narrow feature permission entry for `mock_ad_copy` in `FEATURE_PLAN_REQUIREMENTS`.
- `mock_ad_copy` should be allowed for `standard`, `expert`, and `enterprise`.
- Do not otherwise change auth, token, device, plan, or feature permission logic.

### 5. Propagate request_id into provider_call_log

Update `app/main.py` only if needed to make the existing middleware set:

```python
request.state.request_id = rid
```

The route should pass the same request ID to `execute_provider_call`, so the API response `request_id` and `provider_call_log.request_id` match when `X-Request-ID` is supplied.

If the request has no `X-Request-ID`, it is acceptable for the middleware to generate one and for the route to use it.

### 6. Add focused API tests

Add:

- `cloud-backend/tests/test_mock_ai_api.py`

Required coverage:

- unauthenticated request returns 401.
- authenticated active user/device can call `POST /api/v1/mock-ai/ad-copy`.
- response uses unified wrapper.
- response does not expose `raw_usage`.
- response has backend-computed provider/model/estimated_cost/credits_charged.
- `provider_call_log` receives a success row with:
  - authenticated `user_id`;
  - authenticated `device_id`;
  - feature `mock_ad_copy`;
  - provider `mock`;
  - model `mock-text-v1`;
  - status `success`;
  - `credits_charged=0`.
- `X-Request-ID` is propagated to the response and provider log.
- validation rejects empty or oversized input.
- disabled/banned device behavior is covered if existing fixtures make it cheap.
- no `credit_ledger` row is created.

### 7. Update documentation

Update or add:

- `docs/05-api-contract.md`
- `docs/23-mock-ai-api-endpoint.md`
- `docs/module-context/sprint-02-task-04-mock-ai-api/context.md`
- `tasks/current-task.md`

Optional narrow updates if helpful:

- `docs/06-provider-architecture.md`
- `docs/07-ai-cost-control.md`
- `docs/11-cloud-backend-guide.md`

Docs must clearly state:

- endpoint is mock-only;
- endpoint is authenticated and device-bound;
- no real provider calls occur;
- `credits_charged` remains `0`;
- no `credit_ledger` deduction occurs;
- clients cannot submit provider/model/cost/credit decisions;
- response shape is for MVP/Desktop integration testing.

## What Not To Build

- Do not add real OpenAI, DeepSeek, Claude, ComfyUI, OCR, image, vector, or local provider calls.
- Do not add provider SDKs, dependencies, API keys, env vars, or secrets.
- Do not implement provider routing or model selection from the client.
- Do not implement real credit deduction or `credit_ledger` consumption.
- Do not add payment, recharge, order, grant, monthly quota, expiration, admin, or invoice features.
- Do not modify database DDL or migrations.
- Do not modify provider table/model schema.
- Do not add frontend, desktop, official website, or Tauri code.
- Do not update OpenAPI/shared DTO generation unless explicitly confirmed in a later task.
- Do not broaden GitHub Actions workflows.
- Do not add queues, workers, retry infrastructure, rate limiting infrastructure, or background jobs.
- Do not create a generic prompt execution endpoint.
- Do not let the client submit raw provider prompt, provider name, model name, raw cost, estimated cost, credits charged, user_id, device_id, or final permission decision.

## Allowed Files

Implementation task may modify only:

- `cloud-backend/app/api/v1/mock_ai.py` (new)
- `cloud-backend/app/api/deps.py` (narrow `mock_ad_copy` feature permission only)
- `cloud-backend/app/main.py` (router registration and request_id state propagation only)
- `cloud-backend/app/schemas/mock_ai.py` (new)
- `cloud-backend/tests/test_mock_ai_api.py` (new)
- `docs/05-api-contract.md`
- `docs/23-mock-ai-api-endpoint.md`
- `docs/module-context/sprint-02-task-04-mock-ai-api/context.md`
- `tasks/current-task.md`
- `docs/06-provider-architecture.md` (optional narrow note)
- `docs/07-ai-cost-control.md` (optional narrow note)
- `docs/11-cloud-backend-guide.md` (optional narrow note)

If implementation proves a narrow service helper is required, CC must stop and report why before adding a new service file.

## Forbidden Files

Do not modify:

- `cloud-backend/migrations/ddl/**`
- `cloud-backend/app/models/**`
- `cloud-backend/app/providers/base.py`
- `cloud-backend/app/providers/mock_provider.py`
- `cloud-backend/app/services/cost_service.py`
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/app/services/provider_log_service.py`
- `cloud-backend/app/services/credit_service.py`
- `cloud-backend/tests/test_migrations_integration.py`
- `cloud-backend/tests/conftest_pg.py`
- `cloud-backend/pyproject.toml`
- dependency files or lockfiles
- `.github/workflows/**`
- `.env` or `.env.example`
- `desktop-app/**`
- `official-website/**`
- `shared/**`

## Acceptance Criteria

- `POST /api/v1/mock-ai/ad-copy` exists.
- Endpoint requires auth and bound active device.
- Endpoint validates request body with a dedicated schema.
- Endpoint denies client control over provider/model/cost/credits/user/device.
- Endpoint calls `MockProvider` through `execute_provider_call`.
- Endpoint writes exactly one `provider_call_log` success row on success.
- Provider log includes authenticated user/device and `feature="mock_ad_copy"`.
- API response and provider log share the same request ID when `X-Request-ID` is supplied.
- Response uses unified `{success, data, error, request_id}` wrapper.
- Response does not expose `raw_usage` or raw prompt text.
- `credits_charged` is `0`.
- No `credit_ledger` row is created.
- No real provider SDK, key, env var, dependency, network call, DDL, OpenAPI/shared DTO, frontend, or desktop changes.
- Focused API tests pass.
- Existing backend tests pass.
- `git diff --check` passes.
- Module context is updated with implementation facts and test evidence.

## Test Method

Focused tests:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_mock_ai_api.py -v
```

Backend regression tests:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

Whitespace check:

```bash
cd D:/Project/ad-assistant
git diff --check
```

PostgreSQL migration integration tests are not required for this task because no DDL changes are allowed. Existing PR CI should continue to cover the migration suite.

## Dependency Permission

No new dependencies are allowed.

## Major Change Status

Yes. This task adds one public API endpoint and therefore changes the API contract.

It does not change database schema, real provider integrations, auth/token algorithms, credit/payment runtime deduction, shared DTO/OpenAPI generated artifacts, Tauri permissions, or CI infrastructure.

User confirmation of this task sheet is required before implementation.

## Security Requirements

- Require cloud auth and bound active device.
- Deny unknown features by default; allow only `mock_ad_copy` for this endpoint.
- Do not log raw product text, selling points, prompts, API keys, tokens, or secrets.
- Do not expose `raw_usage` to the client.
- Do not accept provider/model/cost/credits/user/device from the client.
- Keep `credits_charged=0`.
- Do not write `credit_ledger`.
- Keep all errors sanitized.
- Do not create a generic arbitrary prompt execution endpoint.

## Review Instructions For Codex

Review Sprint-02 Task-04 Mock AI API Endpoint.

Focus on:

1. API contract: route path, method, wrapper, schema validation, stable response fields.
2. Auth/device: endpoint is protected and uses authenticated user/device in logs.
3. Provider path: endpoint calls `MockProvider` through `execute_provider_call`.
4. Request ID: response and provider log match when `X-Request-ID` is supplied.
5. Security: no raw prompt/log leakage, no client cost/provider control, no secrets.
6. Credit safety: no deduction and no `credit_ledger` writes.
7. File scope and forbidden-file compliance.
8. Test coverage for auth, success, validation, request ID, logging, and no-ledger behavior.

Output:

- API contract check;
- auth/device check;
- provider/cost/credit check;
- security check;
- test gaps;
- whether commit is allowed.

## Completion Output Required

Implementer must report:

- changed files;
- endpoint path and method;
- request/response schema summary;
- auth/device behavior;
- provider log behavior;
- request_id propagation evidence;
- exact test commands and results;
- confirmation that no DDL/dependency/shared/frontend/desktop changes were made;
- confirmation that no real provider keys/SDKs/network calls were added;
- residual risks;
- whether module context was updated;
- wait for Codex Review, do not self-merge.

## Implementation Evidence (2026-05-31)

- **Branch**: `feature/sprint-02-task-04-mock-ai-api`
- **Base**: main @ `c73f1c2`
- **Test results**:
  - Focused: `21 passed in 4.90s` (`pytest tests/test_mock_ai_api.py -v`)
  - Regression: `147 passed in 18.96s` (`pytest tests/ -v --ignore=tests/test_migrations_integration.py`)
- **Changed files** (11):
  - `cloud-backend/app/api/v1/mock_ai.py` (new)
  - `cloud-backend/app/api/deps.py` (modified — +1 feature entry)
  - `cloud-backend/app/main.py` (modified — +1 line state, +2 lines import/router)
  - `cloud-backend/app/schemas/mock_ai.py` (new)
  - `cloud-backend/tests/test_mock_ai_api.py` (new, 21 tests)
  - `docs/05-api-contract.md` (updated)
  - `docs/23-mock-ai-api-endpoint.md` (updated)
  - `docs/module-context/sprint-02-task-04-mock-ai-api/context.md` (updated)
  - `docs/06-provider-architecture.md` (optional)
  - `docs/07-ai-cost-control.md` (optional)
  - `tasks/current-task.md` (updated)
- **No DDL/dependency changes**: ✅
- **No real provider keys/SDKs/network calls**: ✅
- **No credit_ledger writes**: ✅
- **No forbidden file modified**: ✅
- **Git diff --check**: passed
