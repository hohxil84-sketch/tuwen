# Sprint-02 Summary

Date: 2026-05-31
Base branch: `main`
Current verified head: `8fa3440 docs(rules): add communication and git note conventions (#14)`

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| Task-01 | AI credit account and `credit_ledger` foundation | PR #10 / `fc1c271` |
| Task-02 | PostgreSQL integration test workflow | PR #11 / `96f5d28` |
| Task-03 | Mock Provider foundation | PR #12 / `c73f1c2` |
| Task-04 | Mock AI ad-copy API endpoint | PR #13 / `0cc7f14` |
| Rules | Agent communication and review-scope rules | PR #14 / `8fa3440` |

## Current Cloud API Capability

- Auth/device protected APIs are available from Sprint-01.
- Credit account and `credit_ledger` foundation exist.
- PostgreSQL migration integration checks run in GitHub Actions.
- `MockProvider` exists as a deterministic, network-free Provider implementation.
- `POST /api/v1/mock-ai/ad-copy` is available as a mock-only AI endpoint.
- Mock AI API writes `provider_call_log` with `credits_charged=0`.
- Mock AI API propagates `X-Request-ID` to the response and provider log.

## Current Safety Boundaries

- No real AI Provider SDK, API key, environment variable, or network call has been added.
- No real credit deduction is implemented.
- Mock AI API does not write `credit_ledger`.
- Mock AI API does not expose `raw_usage` to clients.
- Desktop and frontend integration are still separate future tasks.

## Verification

- Task-04 focused tests: `21 passed, 1 warning`.
- Task-04 backend regression: `147 passed, 1 warning`.
- PR #13 CI: `pg-integration` passed.
- PR #14 CI: `pg-integration` passed.
- `git diff --check` passed during local reviews.

## Residual Risks

- `POST /api/v1/mock-ai/ad-copy` is an MVP mock contract; future shape changes should be treated as API contract changes.
- Real Provider routing and model selection remain unimplemented.
- Real credit deduction and pricing remain unimplemented.
- Desktop app has not yet been wired to the cloud mock AI API.

## In Progress

| Task | Scope | Branch |
|------|-------|--------|
| Task-05 | Desktop Mock AI API Client | `feature/sprint-02-task-05-desktop-mock-ai-client` |

Task-05 status (2026-06-01): `IMPLEMENTED_AWAITING_CODEX_REVIEW`
- `npm run build` passes (43 modules, 0 errors)
- `git diff --check` passes
- No backend, dependency, Tauri, or local-service changes
- No frontend automated tests (no test runner in `package.json`; new deps not allowed per task rules)

## Next-Stage Candidate Tasks

These are candidates only. Create a new task document and new branch before implementation.

- Candidate B: API response/OpenAPI/shared DTO generation for the mock AI endpoint.
- Candidate C: Real Provider routing design, still without real billing deduction.
