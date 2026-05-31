# Current Task: Sprint-02 Task-03 Provider Mock Foundation

## Status

`IMPLEMENTED` — implementation complete on branch `feature/sprint-02-task-03-provider-mock`. 24 focused tests pass, 126 regression pass. Awaiting Codex Review before commit and merge.

## Suggested Branch

`feature/sprint-02-task-03-provider-mock`, based on latest `main`.

If a local Git ref permission or slash-name issue occurs, use the flat branch name `sprint-02-task-03-provider-mock`.

## Prerequisites

- Sprint-02 Task-02 credit ledger was merged to `main` by PR #10.
- Infra PostgreSQL CI was merged to `main` by PR #11.
- Latest verified PR #11 merge commit: `96f5d283322ec973db841cf3e10d11f930cd5e09`.
- PR #11 CI evidence: PostgreSQL integration workflow passed with `55 passed, 1 warning`.
- `provider_call_log` exists and has PostgreSQL integration coverage.
- `credit_accounts` and `credit_ledger` exist, but real credit deduction is not part of this task.
- `cloud-backend/app/providers/base.py` is currently only a placeholder.

## Background

The backend already has durable tables for provider call logs and credit ledger entries. The next useful foundation is a real Provider interface plus a deterministic mock provider. This gives future AI features one cloud-side execution path before any real provider SDK, API key, queue, or billing deduction is introduced.

This task must prove that a provider call can:

- use a unified Provider result shape;
- calculate a traceable mock estimated cost;
- write `provider_call_log`;
- avoid logging raw prompts, API keys, or secrets;
- leave `credit_ledger` untouched.

## Major Change Proposal

This task modifies the Provider abstraction and cost-estimation foundation. User confirmation is required before implementation.

1. Reason
   - Replace the placeholder Provider skeleton with a minimal typed interface.
   - Add a deterministic mock provider for local tests and future feature wiring.
   - Prove the provider logging path without real third-party API calls.
   - Prepare for future real provider and credit deduction tasks without combining them.

2. Risks
   - A poorly shaped Provider interface can cause churn when real providers are added.
   - Mock cost values can be mistaken for real billing if docs and names are unclear.
   - Provider logging can accidentally persist raw prompt text or secrets.
   - Adding a public route too early can freeze an API contract before the product flow is ready.

3. Impact
   - Backend provider/service test foundation only.
   - No public API route is required.
   - No database schema change is required.
   - No frontend, desktop, shared DTO, OpenAPI, auth, or device behavior change is required.

4. Rollback
   - Restore `cloud-backend/app/providers/base.py` to the previous placeholder.
   - Delete the mock provider, cost/provider service helpers, and focused tests.
   - Revert the docs added for this task.
   - No database rollback is needed.

5. Backward Compatibility
   - Compatible. Existing API behavior and database schema must remain unchanged.
   - Existing tests should continue to pass.

6. Database Migration
   - None. This task must not add, remove, or edit DDL files.

## What To Build

### 1. Formalize the Provider base interface

Update:

- `cloud-backend/app/providers/base.py`

Required behavior:

- Define a minimal request/result structure for internal provider calls.
- Preserve the unified result fields already documented:
  - `provider`
  - `model`
  - `input_units`
  - `output_units`
  - `image_units`
  - `gpu_seconds`
  - `raw_cost`
  - `estimated_cost`
  - `currency`
  - `result`
  - `raw_usage`
- Define an async provider call interface.
- Validate that usage and cost fields cannot be negative.
- Do not add real provider SDK imports.
- Do not require API keys or environment variables.

Implementation may use standard-library dataclasses or Pydantic models, but must stay consistent with the existing backend style and tests.

### 2. Add MockProvider

Add:

- `cloud-backend/app/providers/mock_provider.py`

Required behavior:

- Deterministic and network-free.
- Uses provider name `mock`.
- Uses a clearly fake model name, for example `mock-text-v1`.
- Produces stable success output for tests.
- Supports a narrow test-only failure path so error logging can be tested.
- Returns usage values and mock cost fields through the unified Provider result shape.
- Does not store raw prompt text inside `raw_usage`.
- Does not read or require provider API keys.

### 3. Add mock cost estimation foundation

Add:

- `cloud-backend/app/services/cost_service.py`

Required behavior:

- Provide a small, explicit mock pricing calculation.
- Make clear in naming/docs that values are mock estimates, not real provider pricing.
- Reject negative units/cost inputs.
- Return nonnegative `estimated_cost`.
- Do not perform credit deduction.
- Do not write `credit_ledger`.

For this task, provider logs may record `credits_charged=0` because real deduction is a later approved task.

### 4. Add provider execution/logging helper

Add:

- `cloud-backend/app/services/provider_service.py`

Required behavior:

- Call `MockProvider`.
- Write `provider_call_log` through the existing provider log service.
- Log both success and controlled mock error cases.
- Include `user_id`, `device_id`, `request_id`, `feature`, provider/model, units, estimated cost, status, error code, and latency where available.
- Do not bypass existing validation in `provider_log_service.py`.
- Do not write `credit_ledger`.
- Do not expose a public HTTP API.

### 5. Add focused tests

Add:

- `cloud-backend/tests/test_provider_mock.py`

Required coverage:

- Provider result has the unified shape.
- MockProvider success is deterministic.
- MockProvider controlled failure is logged with `status="error"` and an `error_code`.
- Provider success writes one `provider_call_log` row.
- `raw_usage` and logged metadata do not contain raw prompt text, API keys, or secrets.
- Cost estimation rejects negative values.
- No `credit_ledger` entry is created by mock provider calls.

Tests should use the existing SQLite test harness unless a current fixture makes that impossible. Do not require PostgreSQL for this task.

### 6. Update documentation

Update or add:

- `docs/06-provider-architecture.md`
- `docs/07-ai-cost-control.md`
- `docs/22-provider-mock-foundation.md`
- `docs/module-context/sprint-02-task-03-provider-mock/context.md`
- `tasks/current-task.md`

Docs must clearly state:

- mock provider is not a real AI provider;
- mock cost estimates are not real billing;
- credit deduction is intentionally out of scope;
- no real provider keys or SDKs are introduced;
- provider calls must be logged through `provider_call_log`.

## What Not To Build

- Do not add OpenAI, DeepSeek, Claude, ComfyUI, OCR, image, or vector provider implementations.
- Do not add real provider SDK dependencies.
- Do not add API keys, secrets, `.env` changes, or new environment variables.
- Do not add a public provider HTTP route.
- Do not modify OpenAPI or shared DTO files.
- Do not modify frontend, desktop, official website, or Tauri files.
- Do not modify auth, device binding, token, or risk-control behavior.
- Do not implement credit deduction, recharge, payment, order, grant, monthly quota, expiration, admin, or invoice features.
- Do not edit database DDL or add migrations.
- Do not broaden GitHub Actions workflows.
- Do not implement provider routing across real vendors.
- Do not add queues, Celery, background workers, or retry infrastructure.

## Allowed Files

Implementation task may modify only:

- `cloud-backend/app/providers/base.py`
- `cloud-backend/app/providers/mock_provider.py` (new)
- `cloud-backend/app/providers/__init__.py`
- `cloud-backend/app/services/cost_service.py` (new)
- `cloud-backend/app/services/provider_service.py` (new)
- `cloud-backend/tests/test_provider_mock.py` (new)
- `docs/06-provider-architecture.md`
- `docs/07-ai-cost-control.md`
- `docs/22-provider-mock-foundation.md`
- `docs/module-context/sprint-02-task-03-provider-mock/context.md`
- `tasks/current-task.md`

If implementation proves a narrow helper export is required, CC must report it before committing and explain why.

## Forbidden Files

Do not modify:

- `cloud-backend/migrations/ddl/**`
- `cloud-backend/app/routes/**`
- `cloud-backend/app/main.py`
- `cloud-backend/app/models.py`
- `cloud-backend/app/services/credit_service.py`
- `cloud-backend/app/services/provider_log_service.py` unless a narrow existing validation bug is found and Codex confirms it before commit
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

- `BaseProvider` or equivalent interface exists and is asynchronous.
- Provider result includes the documented unified usage/cost/result fields.
- `MockProvider` is deterministic and does not perform network access.
- Mock provider success path writes `provider_call_log`.
- Mock provider controlled error path writes `provider_call_log` with `status="error"` and an `error_code`.
- Mock provider logs do not include raw prompt text, API keys, tokens, or secrets.
- Mock cost calculation is explicit, nonnegative, and documented as mock-only.
- No `credit_ledger` row is created by mock provider calls.
- No real provider dependency, SDK, key, or environment variable is added.
- No database DDL or migration file changes.
- No public API route, OpenAPI, or shared DTO changes.
- Focused provider tests pass.
- Existing backend tests pass.
- `git diff --check` passes.
- Module context is updated with implementation facts and test evidence.

## Test Method

Focused tests:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_provider_mock.py -v
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

Yes. This changes the Provider abstraction and introduces a mock provider execution/logging foundation.

It does not change database schema, public API contracts, real provider integrations, auth/token logic, credit/payment runtime logic, shared DTO, OpenAPI, Tauri permissions, or CI infrastructure.

User confirmation of this task sheet is required before implementation.

## Security Requirements

- Never log raw prompt text into `provider_call_log`, `raw_usage`, metadata, exceptions, or test assertions.
- Never add real provider API keys or secret handling.
- Never add client-visible provider credentials.
- Never add network access to third-party AI providers.
- Keep mock error messages sanitized.
- Keep `credits_charged=0` for mock provider logs unless a later approved task implements real deduction.
- Do not expose a public route for arbitrary prompt submission.

## Review Instructions For Codex

Review Sprint-02 Task-03 Provider Mock Foundation.

Focus on:

1. Provider interface shape and future compatibility.
2. Mock-only scope: no real SDKs, keys, network calls, or provider routing.
3. Provider log correctness and sanitized `raw_usage`.
4. Credit safety: no deduction and no `credit_ledger` writes.
5. Cost safety: mock estimates only, nonnegative values, no real pricing claims.
6. File scope and forbidden-file compliance.
7. Test coverage for success, error, logging, and no-ledger behavior.

Output:

- scope check;
- security check;
- cost/credit check;
- provider interface concerns;
- test gaps;
- whether commit is allowed.

## Completion Output Required

Implementer must report:

- changed files;
- provider interface summary;
- mock provider behavior;
- cost calculation summary;
- exact test commands and results;
- confirmation that no DDL/API/dependency files were changed;
- confirmation that no real provider keys/SDKs/network calls were added;
- residual risks;
- whether module context was updated;
- wait for Codex Review, do not self-merge.
