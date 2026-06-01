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
| Task-07 draft | Backend PostgreSQL DateTime Alignment | `feature/sprint-02-task-07-pg-datetime-align` |

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

Task-07 status (2026-06-01): `IMPLEMENTED_AWAITING_REVIEW`
- Goal: align SQLAlchemy models `DateTime(timezone=True)` with DDL `TIMESTAMPTZ`.
- Deliverables:
  - 8 model files updated — all 18 DateTime columns now `DateTime(timezone=True)`.
  - `cloud-backend/scripts/dev_seed_user.py` — docstring updated (mismatch resolved).
  - `docs/25-desktop-mock-e2e-smoke.md` — removed PG bypass, added PG alternative.
  - `docs/11-cloud-backend-guide.md` — updated PG status.
  - `docs/12-database-design.md` — added timestamp alignment note.
  - `docs/sprint-02-summary.md` — this update.
  - `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md` — new.
- Verification: SQLite 147 ✅, PG integration 55 ✅, ORM PG read/write ✅, `git diff --check` ✅.
- This is a major change (model column type declarations) — user confirmed 2026-06-01.
- No DDL, API, service, provider, shared, desktop, dependency, or .env changes.

## Next-Stage Candidate Tasks

These are candidates only. Create a new task document and new branch before implementation.

- Candidate A: Desktop Mock AI E2E smoke verification and local runbook.
- Candidate B: API response/OpenAPI/shared DTO generation for the mock AI endpoint.
- Candidate C: Real Provider routing design, still without real billing deduction.
