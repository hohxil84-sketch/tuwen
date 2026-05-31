# Module Context: Sprint-02 Task-03 Provider Mock Foundation

## Status

`MERGED` - PR #12 merged to `main`.

## Branch

- Implementation branch: `feature/sprint-02-task-03-provider-mock`
- PR: #12
- Merge commit: `c73f1c2`
- Feature commit: `34b1528`

## Implementation Evidence (2026-05-31)

- **Test results**:
  - Focused: `24 passed in 1.24s` (`pytest tests/test_provider_mock.py -v`)
  - Regression: `126 passed in 14.28s` (`pytest tests/ -v --ignore=tests/test_migrations_integration.py`)
- **Changed files**:
  - `cloud-backend/app/providers/base.py`
  - `cloud-backend/app/providers/mock_provider.py`
  - `cloud-backend/app/providers/__init__.py` (unchanged except for new modules existing in package)
  - `cloud-backend/app/services/cost_service.py`
  - `cloud-backend/app/services/provider_service.py`
  - `cloud-backend/tests/test_provider_mock.py`
  - `docs/06-provider-architecture.md`
  - `docs/07-ai-cost-control.md`
  - `docs/22-provider-mock-foundation.md`
  - `docs/module-context/sprint-02-task-03-provider-mock/context.md`
  - `tasks/current-task.md`
- **No DDL/API/dependency changes**: ✅
- **No real provider keys/SDKs/network calls**: ✅
- **No credit_ledger writes**: ✅ confirmed by tests
- **Git diff --check**: passed

## Task Summary

Add the first backend Provider execution foundation:

- typed async Provider interface;
- deterministic mock provider;
- mock-only cost estimate helper;
- internal provider execution/logging helper;
- focused provider tests.

The task must prove provider calls can be logged without real provider SDKs, network calls, API keys, public routes, DDL changes, or credit deduction.

## Allowed Files

- `cloud-backend/app/providers/base.py`
- `cloud-backend/app/providers/mock_provider.py`
- `cloud-backend/app/providers/__init__.py`
- `cloud-backend/app/services/cost_service.py`
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/tests/test_provider_mock.py`
- `docs/06-provider-architecture.md`
- `docs/07-ai-cost-control.md`
- `docs/22-provider-mock-foundation.md`
- `docs/module-context/sprint-02-task-03-provider-mock/context.md`
- `tasks/current-task.md`

## Forbidden Areas

- DDL and migrations.
- Public API routes.
- OpenAPI and shared DTO.
- Frontend, desktop, official website, Tauri.
- Auth, device binding, token behavior.
- Real provider SDKs, API keys, secrets, environment variables.
- Credit deduction, recharge, payment, order, grant, monthly quota, expiration, admin workflows.
- GitHub Actions workflows.

## Required Tests

Focused:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_provider_mock.py -v
```

Regression:

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

Whitespace:

```bash
cd D:/Project/ad-assistant
git diff --check
```

## Review Checklist

- Provider result includes unified fields.
- MockProvider is deterministic and network-free.
- Success and controlled error paths write `provider_call_log`.
- Raw prompt text and secrets are not logged.
- Cost values are mock-only and nonnegative.
- `credit_ledger` remains untouched.
- No real provider dependencies or keys are introduced.
- No DDL/API/DTO/frontend/desktop files are modified.

## Residual Risks To Track

- Provider interface may need adjustment when the first real provider is implemented.
- Mock estimated cost must not be interpreted as product pricing.
- Provider logging must remain sanitized when future prompt-bearing workflows are added.
- Real credit deduction still needs a separate approved task.
