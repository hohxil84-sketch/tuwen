# Development Record

## 2026-05-31

### Sprint-02 Task-04 Mock AI API Endpoint

- Branch: `feature/sprint-02-task-04-mock-ai-api`
- PR: #13
- Merge commit: `0cc7f14`
- Feature commit: `6a40445`
- Scope: added protected `POST /api/v1/mock-ai/ad-copy`.
- Key behavior: auth/device protected, checks plan and `mock_ad_copy`, calls `MockProvider` through `execute_provider_call`, writes `provider_call_log`, propagates `X-Request-ID`, returns unified wrapper.
- Safety: no real Provider SDK, no API key, no network call, no DDL, no dependency change, no frontend/desktop change, no `credit_ledger` write.
- Tests: `21 passed, 1 warning` focused; `147 passed, 1 warning` backend regression; PR #13 `pg-integration` passed.

### Agent Rules Update

- Branch: `docs/rules`
- PR: #14
- Merge commit: `8fa3440`
- Commit: `0e864b7`
- Scope: added communication and Git note rules for Codex / Claude Code / DeepSeek.
- Rules: address user as "大哥"; commit/push/PR/handoff notes use Chinese and English bilingual notes; Codex Review output includes CC-forwardable next-step instructions in Chinese.
- Tests: PR #14 `pg-integration` passed.

## 2026-06-01

### Sprint-02 Task-05 Desktop Mock AI API Client

- Branch: `feature/sprint-02-task-05-desktop-mock-ai-client`
- PR: #16
- Merge commit: `42dbad8`
- Feature commit: `89b901a`
- Scope: added desktop cloud API client, memory-only auth store, login UI, and login-gated Mock AI ad-copy panel on the OCR page.
- Key behavior: desktop calls `POST /api/v1/auth/login`, best-effort `POST /api/v1/auth/logout` with `refresh_token`, and `POST /api/v1/mock-ai/ad-copy`; mock response displays provider, model, `credits_charged`, and backend `request_id`.
- Safety: tokens are memory-only; no localStorage/sessionStorage/IndexedDB/SQLite/cookies/files/Tauri storage; no API keys; no third-party AI calls; no client-side provider/model/cost/credit decisions.
- Tests: `npm run build` passed in `desktop-app` with 43 modules and 0 errors; `git diff --check main..HEAD` passed after commit `89b901a`; PR #16 `pg-integration` passed.
- Residual risk: live manual verification was not completed because local PostgreSQL/backend service was not available during review.
