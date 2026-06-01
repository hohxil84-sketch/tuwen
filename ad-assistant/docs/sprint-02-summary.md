# Sprint-02 Summary

Date: 2026-06-01
Base branch: `main`
Current verified head: `4708379 Merge pull request #24 from hohxil84-sketch/docs/cc-confirmed-merge-rule`

**Sprint-02 is closed.** All 9 tasks + 2 workflow/docs PRs merged to `main`.

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| Task-01 | AI credit account and `credit_ledger` foundation | PR #10 / `fc1c271` |
| Task-02 | PostgreSQL integration test workflow | PR #11 / `96f5d28` |
| Task-03 | Mock Provider foundation | PR #12 / `c73f1c2` |
| Task-04 | Mock AI ad-copy API endpoint | PR #13 / `0cc7f14` |
| Rules | Agent communication and review-scope rules | PR #14 / `8fa3440` |
| Task-05 | Desktop Mock AI API Client | PR #16 / `42dbad8` |
| Task-06 | Desktop Mock AI E2E Smoke Verification | PR #18 / `cfbadeb` |
| Task-07 | PostgreSQL DateTime alignment (ORM/DDL) | PR #20 / `1a3602f` |
| Task-08 | Mock AI API Contract Formalization | PR #22 / `6fc40a8` |
| Task-09 | Provider Routing Design | PR #23 / `37e0430` |
| Workflow | CC autonomous development rules | PR #21 / `fe5e94f` |
| Workflow | User-confirmed PR merge by CC | PR #24 / `4708379` |

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
- Task-07 backend regression: `147 passed` (SQLite) + `55 passed` (PG DDL integration).
- Task-07 ORM `create_all` against PG: succeeded.
- Task-07 `dev_seed_user.py` against PG: user created + device bound.
- Task-08 backend regression: `147 passed` + `21 passed` (mock AI).
- Task-08 FastAPI OpenAPI gen: `MockAdCopyData` + `APIResponse_MockAdCopyData_` + path verified.
- Task-08 wire response unchanged: yes.
- Task-09 backend: `147 passed` (regression) + `21 passed` (mock AI) + `20 passed` (routing) = `167 total`.
- Task-09 FastAPI OpenAPI gen: unchanged.
- Task-09 wire response unchanged: yes.
- Task-05 desktop build: `npm run build` passed with 43 modules transformed and 0 errors.
- All PRs CI: `pg-integration` passed.
- `git diff --check` passed during all local reviews.

## Residual Risks

- `POST /api/v1/mock-ai/ad-copy` is an MVP mock contract; future shape changes should be treated as API contract changes.
- Real Provider routing and model selection remain unimplemented.
- Real credit deduction and pricing remain unimplemented.
- Task-05 live manual verification remains incomplete because the local PostgreSQL/backend environment was not available during review.

## Sprint-02 Closeout

All planned Sprint-02 tasks are merged. No tasks remain in progress.

Key deliverables across the sprint:
- Credit account + `credit_ledger` foundation (not yet wired for real deduction).
- PostgreSQL migration integration test workflow in CI.
- Mock Provider + Mock AI ad-copy API endpoint with typed contract.
- Desktop mock AI client (login-gated, memory-only tokens).
- E2E smoke runbook + dev seed script.
- ORM `DateTime(timezone=True)` aligned with DDL `TIMESTAMPTZ`.
- `APIResponse[T]` generic + first OpenAPI spec + first TypeScript DTO.
- `ProviderRegistry` + `ProviderRouter` + `route_and_execute_provider_call()` routing layer.

All routes still resolve to `MockProvider`. No real AI Provider SDKs, API keys, or network calls exist yet.

## Next-Stage (Sprint-03 Candidates)

These are candidates only. Create a new task document and new branch before implementation.

- Real Provider integration (DeepSeek / OpenAI / Claude SDK, API keys, network calls).
- Real credit deduction wired to `credit_ledger` and `provider_call_log`.
- Membership / package / payment / recharge / grant-balance flows.
- Provider fallback / retry / health-check mechanisms.
- Backend admin query and reporting capability.
- Local OCR history retention, cleanup, and privacy policy.
