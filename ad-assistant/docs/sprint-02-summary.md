# Sprint-02 Summary

Date: 2026-06-01
Base branch: `main`
Current verified head: `42dbad8 Merge pull request #16 from hohxil84-sketch/feature/sprint-02-task-05-desktop-mock-ai-client`

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| Task-01 | AI credit account and `credit_ledger` foundation | PR #10 / `fc1c271` |
| Task-02 | PostgreSQL integration test workflow | PR #11 / `96f5d28` |
| Task-03 | Mock Provider foundation | PR #12 / `c73f1c2` |
| Task-04 | Mock AI ad-copy API endpoint | PR #13 / `0cc7f14` |
| Rules | Agent communication and review-scope rules | PR #14 / `8fa3440` |
| Task-05 | Desktop Mock AI API Client | PR #16 / `42dbad8` |

## Current Cloud API Capability

- Auth/device protected APIs are available from Sprint-01.
- Credit account and `credit_ledger` foundation exist.
- PostgreSQL migration integration checks run in GitHub Actions.
- `MockProvider` exists as a deterministic, network-free Provider implementation.
- `POST /api/v1/mock-ai/ad-copy` is available as a mock-only AI endpoint.
- Mock AI endpoint now has a typed `response_model=APIResponse[MockAdCopyData]` and machine-readable contract (`shared/openapi/mock-ai.yaml`, `shared/dto/mock-ai.ts`).
- Mock AI API writes `provider_call_log` with `credits_charged=0`.
- Mock AI API propagates `X-Request-ID` to the response and provider log.
- Desktop app has a narrow cloud API client for login/logout/mock ad-copy.
- Desktop tokens are memory-only for Task-05 and are not persisted to browser storage, files, SQLite, cookies, or Tauri storage.
- Desktop OCR page has a login-gated Mock AI ad-copy panel that displays backend `request_id`, provider, model, and `credits_charged`.

## Current Safety Boundaries

- No real AI Provider SDK, API key, environment variable, or network call has been added.
- No real credit deduction is implemented.
- Mock AI API does not write `credit_ledger`.
- Mock AI API does not expose `raw_usage` to clients.
- Desktop Mock AI integration is mock-only and does not add real provider calls, client-side provider selection, real credit deduction, API keys, or third-party AI network calls.

## Verification

- Task-04 focused tests: `21 passed, 1 warning`.
- Task-04 backend regression: `147 passed, 1 warning`.
- PR #13 CI: `pg-integration` passed.
- PR #14 CI: `pg-integration` passed.
- PR #16 CI: `pg-integration` passed.
- Task-05 desktop build: `npm run build` passed with 43 modules transformed and 0 errors.
- Task-05 whitespace check: `git diff --check main..HEAD` passed after commit `89b901a`.
- `git diff --check` passed during local reviews.

## Residual Risks

- `POST /api/v1/mock-ai/ad-copy` is an MVP mock contract; future shape changes should be treated as API contract changes.
- Real Provider routing and model selection remain unimplemented.
- Real credit deduction and pricing remain unimplemented.
- Task-05 live manual verification remains incomplete because the local PostgreSQL/backend environment was not available during review.

## In Progress

| Task | Scope | Branch |
|------|-------|--------|
| Task-06 draft | Desktop Mock AI E2E Smoke Verification | `feature/sprint-02-task-06-desktop-mock-e2e-smoke` |
| Task-08 draft | Mock AI API Contract Formalization | `feature/sprint-02-task-08-mock-ai-api-contract` |
| Task-09 draft | Provider Routing Design | `feature/sprint-02-task-09-provider-routing` |

Task-09 status (2026-06-01): `IMPLEMENTED_AWAITING_REVIEW`
- Goal: build provider routing infrastructure (ProviderRegistry + ProviderRouter + route_and_execute)
- Deliverables:
  - `cloud-backend/app/providers/registry.py` — ProviderRegistry (named container)
  - `cloud-backend/app/providers/router.py` — ProviderRouter ((feature, plan) → provider)
  - `cloud-backend/app/services/provider_service.py` — added `route_and_execute_provider_call()`
  - `cloud-backend/app/api/v1/mock_ai.py` — uses routing (no more direct MockProvider import)
  - `cloud-backend/app/providers/__init__.py` — updated docstring
  - `cloud-backend/tests/test_provider_routing.py` — 20 focused tests
  - `docs/06-provider-architecture.md` — added routing layer section
  - `docs/sprint-02-summary.md` — this update
- This is a major change (Provider interface call path per CODEX.md).
- All routes still resolve to MockProvider — no real provider SDKs/keys/network calls.
- `execute_provider_call()` unchanged — backward compatible.
- Wire response unchanged — desktop mock client needs zero changes.

Task-08 status (2026-06-01): `IMPLEMENTED_AWAITING_REVIEW`
- Goal: wire `response_model=APIResponse[MockAdCopyData]`, create `shared/openapi/mock-ai.yaml`, create `shared/dto/mock-ai.ts`
- Deliverables:
  - `cloud-backend/app/schemas/common.py` — generic `APIResponse[T]`
  - `cloud-backend/app/api/v1/mock_ai.py` — wired `response_model`
  - `shared/openapi/mock-ai.yaml` — first OpenAPI spec
  - `shared/dto/mock-ai.ts` — first TypeScript DTO
  - `docs/23-mock-ai-api-endpoint.md` — updated with OpenAPI/DTO references
  - `docs/05-api-contract.md` — noted first spec created
  - `docs/sprint-02-summary.md` — this update
- This is a major change (API contract / shared DTO / OpenAPI per CODEX.md).
- Wire response is unchanged — desktop mock client needs zero changes.
- No new dependencies, no DDL changes, no other endpoint changes.

Task-06 status (2026-06-01): `IMPLEMENTED_AWAITING_REVIEW`
- Goal: make the merged Task-05 desktop mock MVP path reproducible and manually verified.
- Deliverables:
  - `docs/25-desktop-mock-e2e-smoke.md` — E2E smoke runbook with exact commands.
  - `cloud-backend/scripts/dev_seed_user.py` — dev-only seed script.
  - `docs/09-desktop-app-guide.md` — updated with dev runbook reference.
  - `docs/11-cloud-backend-guide.md` — updated with dev setup section.
  - `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md` — module context.
- Verification: `npm run build` ✅ (43 modules, 0 errors), `git diff --check` ✅, backend 147 tests ✅.
- Known issues found: DDL TIMESTAMPTZ / ORM DateTime mismatch (documented, fixed in Task-07).
- No production backend/API/DDL/dependency/shared/Tauri/desktop source changes were made.
- No secrets or real provider integrations were added.

## Next-Stage Candidate Tasks

These are candidates only. Create a new task document and new branch before implementation.

- Candidate A: Desktop Mock AI E2E smoke verification and local runbook.
