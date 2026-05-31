# 22 Provider Mock Foundation

## Purpose

This document defines Sprint-02 Task-03: Provider Mock Foundation.

The goal is to introduce a minimal cloud-side Provider abstraction and deterministic mock provider before any real AI provider integration. The task should prove the provider execution and logging path while keeping billing, public API, and third-party provider work out of scope.

## Current State

- `provider_call_log` already exists and is covered by migration tests.
- `credit_accounts` and `credit_ledger` already exist.
- `cloud-backend/app/providers/base.py` is currently only a placeholder.
- There is no real provider implementation yet.
- Real credit deduction is not implemented yet.
- PostgreSQL migration integration tests are now covered by GitHub Actions from PR #11.

## Major Change

This task is a major change because it defines the Provider interface shape and introduces the first provider execution path.

It is intentionally narrow:

- mock provider only;
- mock cost estimate only;
- provider logging only;
- no real provider calls;
- no public API route;
- no credit deduction;
- no DDL changes.

## Scope

The implementation should add:

- a typed async Provider interface;
- a deterministic `MockProvider`;
- a mock-only cost estimation helper;
- an internal provider execution/logging helper;
- focused tests for success, controlled error logging, sanitized usage, and no credit ledger writes.

## Provider Result Shape

All providers must eventually return a unified result shape:

```json
{
  "provider": "mock",
  "model": "mock-text-v1",
  "input_units": 0,
  "output_units": 0,
  "image_units": 0,
  "gpu_seconds": 0,
  "raw_cost": 0.0,
  "estimated_cost": 0.0,
  "currency": "CNY",
  "result": {},
  "raw_usage": {}
}
```

Task-03 should make this shape concrete in backend code and tests. It should not add fields that force a public API contract.

## Mock Cost Rules

Mock cost values must be:

- deterministic;
- nonnegative;
- explicitly documented as mock estimates;
- not treated as real provider pricing;
- not used to deduct user credits.

For Task-03, provider logs may record `credits_charged=0`. Real conversion from provider cost to user credit deduction belongs to a later task.

## Logging Rules

Provider calls must be recorded through the existing provider log service.

Success logs should include:

- user/device/request identifiers;
- feature;
- provider and model;
- usage units;
- estimated cost;
- `status="success"`;
- latency if available.

Controlled mock failures should include:

- `status="error"`;
- sanitized `error_code`;
- no raw prompt text;
- no API keys, tokens, or secrets.

## Security Rules

Task-03 must not:

- read real provider API keys;
- add secrets or environment variables;
- call external AI providers;
- log raw prompt text;
- expose a prompt-submission HTTP endpoint;
- write `credit_ledger`;
- modify DDL files.

## Test Expectations

Required focused command:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_provider_mock.py -v
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

PostgreSQL migration integration tests are not required for this task because no DDL changes are allowed.

## Non-Goals

- Real OpenAI, DeepSeek, Claude, ComfyUI, OCR, image, or vector provider integration.
- Provider routing across real vendors.
- Public API route.
- OpenAPI or shared DTO changes.
- Credit deduction, recharge, payment, order, grant, monthly quota, or admin workflows.
- New dependencies.
- New GitHub Actions workflow.
- Database migration.

## Implementation Evidence (2026-05-31)

- **Implementation branch**: `feature/sprint-02-task-03-provider-mock`
- **Head commit**: `(pending — awaiting Codex review)`
- **Changed files**:
  - `cloud-backend/app/providers/base.py` — 定型 Provider 接口（`ProviderRequest`, `ProviderResult`, `AsyncProvider`）
  - `cloud-backend/app/providers/mock_provider.py` — 确定性 MockProvider
  - `cloud-backend/app/services/cost_service.py` — mock 成本估算
  - `cloud-backend/app/services/provider_service.py` — Provider 执行/日志服务
  - `cloud-backend/tests/test_provider_mock.py` — 24 个聚焦测试
  - `docs/06-provider-architecture.md`
  - `docs/07-ai-cost-control.md`
  - `docs/22-provider-mock-foundation.md`
  - `docs/module-context/sprint-02-task-03-provider-mock/context.md`
  - `tasks/current-task.md`
- **Test results**:
  - Focused: `24 passed` (`pytest tests/test_provider_mock.py -v`)
  - Regression: `126 passed` (`pytest tests/ -v --ignore=tests/test_migrations_integration.py`)
- **No DDL/API/dependency changes**: ✅ confirmed
- **No real provider keys/SDKs/network calls**: ✅ confirmed

## Review Gate

After CC implementation, Codex should review before commit approval.

Review focus:

- provider interface compatibility;
- mock-only boundary;
- sanitized logging;
- no credit ledger writes;
- no real provider dependency or network access;
- focused tests and backend regression results;
- allowed-file compliance.
