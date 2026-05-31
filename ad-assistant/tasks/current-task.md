# Current Task: Sprint-02 Task-05 Desktop Mock AI API Client

## Status

`IMPLEMENTED_CODEX_APPROVED`

Implementation completed on 2026-06-01 on branch `feature/sprint-02-task-05-desktop-mock-ai-client`.

Base: `main` @ `8fa3440`.

Codex Review passed all 3 iterations. Commit authorized on 2026-06-01.

## Suggested Branch

`feature/sprint-02-task-05-desktop-mock-ai-client`, based on latest `main`.

If a local Git ref permission or slash-name issue occurs, use the flat branch name `sprint-02-task-05-desktop-mock-ai-client`.

## Prerequisites

- Latest verified `main`: `8fa3440` (`docs(rules): add communication and git note conventions (#14)`).
- Sprint-02 Task-04 was merged by PR #13 as `0cc7f14`.
- `POST /api/v1/mock-ai/ad-copy` exists in cloud backend.
- The endpoint requires auth, active bound device, valid plan, and `mock_ad_copy` feature permission.
- The endpoint returns unified `{success, data, error, request_id}` response.
- The endpoint is mock-only, writes `provider_call_log`, charges `0`, and does not write `credit_ledger`.
- Desktop app currently has minimal Vue pages and local OCR service calls, but no cloud API client or real login UI.

## Background

The backend now exposes a protected mock AI endpoint that is safe for MVP integration testing. The next small product step is to let the desktop app call this backend endpoint through a narrow cloud API client.

This task is a desktop integration slice only. It proves login/session-in-memory, device-bound cloud auth, and a mock ad-copy request from the desktop UI without adding real AI providers, real billing, persistent token storage, or backend changes.

## Major Change Proposal

This task touches desktop auth/session handling and calls a protected cloud API from the desktop app. User confirmation is required before implementation.

1. Reason
   - Connect the desktop MVP to the already-merged cloud mock AI endpoint.
   - Replace pure placeholder UI with a minimal authenticated cloud call path.
   - Prove desktop-to-cloud request/response handling before real provider or billing work.

2. Risks
   - Desktop token handling can become unsafe if tokens are persisted in local storage or logs.
   - A hard-coded cloud URL can make local testing brittle.
   - UI could accidentally suggest real AI generation even though the endpoint is mock-only.
   - Client-side feature or plan assumptions could drift from server-side authorization.

3. Impact
   - Adds a small desktop cloud API service layer.
   - Adds in-memory desktop auth/session state.
   - Updates desktop UI to login and call `POST /api/v1/mock-ai/ad-copy`.
   - Adds focused frontend tests if the existing toolchain can support them without new dependencies; otherwise documents manual verification.
   - No backend schema, API contract, provider, credit, payment, shared DTO, or OpenAPI changes.

4. Rollback
   - Remove the desktop cloud API service and auth/session store.
   - Revert the desktop page/router changes.
   - Remove focused tests and documentation for this task.
   - No database rollback is needed.

5. Backward Compatibility
   - Compatible. Existing backend APIs remain unchanged.
   - Existing local OCR page and service must keep working.

6. Database Migration
   - None. This task must not add, remove, or edit cloud or desktop database migrations.

## What To Build

### 1. Add a desktop cloud API service

Add:

- `desktop-app/src/services/cloudApi.ts`

Required behavior:

- Define typed request/response helpers for:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/logout` if useful and cheap
  - `POST /api/v1/mock-ai/ad-copy`
- Use the backend unified response shape.
- Send `Authorization: Bearer <access_token>` only after login.
- Include the backend-assigned `request_id` in the mock ad-copy return value so the UI can display it.
- Read the base URL from `import.meta.env.VITE_CLOUD_API_BASE_URL`, with default `http://127.0.0.1:8000`.
- Never call OpenAI, DeepSeek, Claude, ComfyUI, or any third-party AI API.
- Never accept provider, model, cost, credits, user ID, device ID, plan, or permission decisions from the UI.
- Never log access tokens, refresh tokens, passwords, device fingerprints, or request bodies containing user-entered product text.

### 2. Add in-memory auth/session state

Add:

- `desktop-app/src/stores/authStore.ts`

Required behavior:

- Store access token, refresh token, user info, and device info in memory only.
- Provide login/logout helpers that call the cloud API service.
- Provide an authenticated mock ad-copy call helper or expose token state for the page service call.
- Do not use `localStorage`, `sessionStorage`, IndexedDB, SQLite, cookies, Tauri secure storage, or files for token persistence in this task.
- Do not implement automatic token refresh unless already required by the simplest login flow.
- Do not implement account registration, password reset, device management, subscription purchase, or admin flows.

### 3. Update the desktop UI

Update:

- `desktop-app/src/pages/LoginPage.vue`
- `desktop-app/src/pages/OcrPage.vue`
- `desktop-app/src/router.ts` if a small route guard or link is needed
- `desktop-app/src/App.vue` only if needed for shared navigation/status

Required behavior:

- Login page accepts account, password, and device fingerprint.
- Login page calls cloud auth and keeps tokens in memory only.
- UI clearly labels the mock AI result as mock/test output.
- OCR page keeps the existing local OCR workflow.
- OCR page may add a small "Mock AI ad copy" panel using user-entered:
  - product name
  - selling points
  - platform
  - tone
- Mock AI panel calls `POST /api/v1/mock-ai/ad-copy` only after login.
- Display returned `text`, `provider`, `model`, `credits_charged`, and `request_id`.
- Show sanitized error messages for 401/403/422/network failures.
- Do not add a generic prompt execution UI.
- Do not let the user choose provider/model/cost/credits.

### 4. Add focused frontend tests if feasible

Preferred additions:

- `desktop-app/tests/cloudApi.test.ts`
- `desktop-app/tests/authStore.test.ts`

Required coverage if tests are added:

- cloud API service builds correct endpoint URLs.
- mock ad-copy call sends Bearer token and no provider/model/cost/credit fields.
- auth store does not persist tokens to browser storage.
- non-success unified responses become sanitized errors.

If the current desktop toolchain cannot run tests without new dependencies, do not add dependencies. Instead, document manual verification steps in the completion output.

### 5. Update documentation

Update or add:

- `docs/24-desktop-mock-ai-api-client.md`
- `docs/module-context/sprint-02-task-05-desktop-mock-ai-client/context.md`
- `docs/09-desktop-app-guide.md`
- `docs/sprint-02-summary.md`
- `tasks/current-task.md`

Docs must clearly state:

- desktop integration is mock-only;
- tokens are memory-only in this task;
- no real provider calls occur;
- no real credit deduction occurs;
- the server remains the authority for auth, plan, feature permission, provider, model, cost, and credits;
- desktop must not store API keys or call third-party AI APIs.

## What Not To Build

- Do not add real OpenAI, DeepSeek, Claude, ComfyUI, OCR, image, vector, or local provider calls.
- Do not add provider SDKs, dependencies, API keys, env vars containing secrets, or third-party AI network calls.
- Do not implement provider routing or model selection from the client.
- Do not implement real credit deduction or `credit_ledger` consumption.
- Do not add payment, recharge, order, grant, monthly quota, expiration, admin, invoice, registration, password reset, or subscription flows.
- Do not modify cloud backend code, cloud backend tests, DDL, migrations, models, Provider services, auth/token algorithms, or credit services.
- Do not update OpenAPI/shared DTO generation.
- Do not broaden GitHub Actions workflows.
- Do not modify Tauri permissions, auto-update, filesystem permissions, or local Python service startup.
- Do not persist tokens in localStorage, sessionStorage, IndexedDB, SQLite, files, or logs.
- Do not create a generic prompt execution UI or arbitrary AI workflow UI.
- Do not modify official website code.

## Allowed Files

Implementation task may modify only:

- `desktop-app/src/services/cloudApi.ts` (new)
- `desktop-app/src/stores/authStore.ts` (new)
- `desktop-app/src/pages/LoginPage.vue`
- `desktop-app/src/pages/OcrPage.vue`
- `desktop-app/src/router.ts`
- `desktop-app/src/App.vue`
- `desktop-app/src/env.d.ts` (only for `VITE_CLOUD_API_BASE_URL` typing if needed)
- `desktop-app/tests/cloudApi.test.ts` (new, optional if no new dependencies are needed)
- `desktop-app/tests/authStore.test.ts` (new, optional if no new dependencies are needed)
- `docs/24-desktop-mock-ai-api-client.md`
- `docs/module-context/sprint-02-task-05-desktop-mock-ai-client/context.md`
- `docs/09-desktop-app-guide.md`
- `docs/sprint-02-summary.md`
- `tasks/current-task.md`

If implementation proves another desktop file is required, CC must stop and report why before modifying it.

## Forbidden Files

Do not modify:

- `cloud-backend/**`
- `shared/**`
- `official-website/**`
- `.github/workflows/**`
- `desktop-app/src-tauri/**`
- `desktop-app/local-service/**`
- `desktop-app/local-tools/**`
- `desktop-app/migrations/**`
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- dependency files or lockfiles
- `.env` or `.env.example`
- files containing secrets

## Acceptance Criteria

- Desktop app can perform a cloud login with account/password/device fingerprint.
- Tokens remain memory-only and are not persisted to browser storage, files, SQLite, or logs.
- Desktop app can call `POST /api/v1/mock-ai/ad-copy` after login.
- Mock AI request does not include provider, model, cost, credits, user_id, device_id, plan, or permission decisions.
- UI displays mock ad-copy text and key computed fields from backend response, including the real backend-assigned `request_id`.
- UI clearly marks the output as mock/test output.
- Existing local OCR upload, OCR result display, and OCR history behavior are not intentionally broken.
- Cloud backend code, DDL, Provider code, credit code, shared DTO/OpenAPI, Tauri permissions, and dependencies remain unchanged.
- No third-party AI SDK, API key, secret, or network call is added.
- `npm run build` passes in `desktop-app`.
- If focused frontend tests are added, they pass.
- `git diff --check` passes.
- Module context is updated with implementation facts and verification evidence.

## Test Method

Desktop build:

```bash
cd D:/Project/ad-assistant/desktop-app
npm run build
```

Focused tests: Skipped — `desktop-app/package.json` has no test script, and new dependencies are not allowed per task rules.

```text
1. Start cloud backend locally.
2. Start desktop Vite dev server.
3. Login with a valid test user and device fingerprint.
4. Submit a mock ad-copy request.
5. Confirm UI shows mock result, provider=mock, model=mock-text-v1, credits_charged=0, and request_id.
6. Refresh the desktop page and confirm token state is gone.
7. Verify existing OCR upload/recognition/history behavior is not broken.
```

Whitespace check:

```bash
cd D:/Project/ad-assistant
git diff --check
```

Backend regression tests are not required for this task because backend files are forbidden. If any backend file is touched, stop and request a new task scope.

## Dependency Permission

No new dependencies are allowed.

Do not edit `desktop-app/package.json` or `desktop-app/package-lock.json`.

## Major Change Status

Yes. This task adds desktop auth/session handling and a new cloud API call path.

It does not change the backend API contract, database schema, Provider interface, real provider integrations, credit/payment runtime deduction, shared DTO/OpenAPI generated artifacts, Tauri permissions, local Python service startup, or CI infrastructure.

User confirmation of this task sheet is required before implementation.

## Security Requirements

- Keep tokens memory-only for this task.
- Do not log tokens, passwords, device fingerprints, raw request bodies, or secrets.
- Do not store tokens in localStorage, sessionStorage, IndexedDB, SQLite, cookies, files, or Tauri storage.
- Do not send API keys to the client.
- Do not let the client decide plan, feature permission, provider, model, cost, or credits.
- Do not call third-party AI APIs from the desktop app.
- Keep all mock AI errors sanitized.
- Make mock-only status visible in UI copy.

## Review Instructions For Codex

Review Sprint-02 Task-05 Desktop Mock AI API Client.

Focus on:

1. Desktop token safety: memory-only, no persistence, no logs.
2. Cloud API call shape: endpoint path, auth header, unified response handling.
3. Client authority boundaries: no provider/model/cost/credits/plan decisions from UI.
4. Mock-only clarity: no real AI provider calls or misleading UI.
5. File scope and forbidden-file compliance.
6. Existing OCR behavior is not broken by the UI changes.
7. Test/build evidence and manual verification completeness.

Output:

- token/session safety check;
- desktop API contract check;
- provider/cost/credit boundary check;
- UI/mock-only check;
- test gaps;
- whether commit is allowed.

## Completion Output Required

Implementer must report:

- changed files;
- login/session behavior;
- mock AI request/response behavior;
- token storage confirmation;
- exact test commands and results;
- manual verification steps and results if no frontend tests were added;
- confirmation that no backend/DDL/dependency/shared/Tauri/local-service changes were made;
- confirmation that no real provider keys/SDKs/network calls were added;
- residual risks;
- whether module context was updated;
- wait for Codex Review, do not self-merge.

---

## Implementation Evidence (2026-06-01, iteration 1 fixes)

### Changed Files

| Type | File |
|------|------|
| 🆕 New | `desktop-app/src/services/cloudApi.ts` |
| 🆕 New | `desktop-app/src/stores/authStore.ts` |
| ✏ Modified | `desktop-app/src/pages/LoginPage.vue` |
| ✏ Modified | `desktop-app/src/pages/OcrPage.vue` |
| ✏ Modified | `desktop-app/src/App.vue` |
| ✏ Modified | `desktop-app/src/router.ts` |
| ✏ Modified | `desktop-app/src/env.d.ts` |
| 📄 New/Updated | `docs/24-desktop-mock-ai-api-client.md` |
| 📄 Updated | `docs/module-context/sprint-02-task-05-desktop-mock-ai-client/context.md` |
| 📄 Updated | `docs/09-desktop-app-guide.md` |
| 📄 Updated | `docs/sprint-02-summary.md` |
| 📄 Updated | `tasks/current-task.md` |

### request_id Fix (Codex Review iteration 1)

- `cloudApi.ts`: Added `MockAdCopyResponse` interface that extends `MockAdCopyData` with `request_id`. `mockAdCopy()` now returns `{ ...response.data, request_id: response.request_id }` — the real backend-assigned request_id from the unified response envelope.
- `authStore.ts`: `callMockAdCopy()` return type updated to `MockAdCopyResponse`.
- `OcrPage.vue`: Removed placeholder `"见服务端响应"`. Uses `mockResult.request_id` directly from the `MockAdCopyResponse` type.

### Router Comment Fix (Codex Review iteration 1)

- `router.ts`: Comment now accurately describes that no router-level auth guard was added. Pages check auth state internally via Pinia authStore.

### Type Alignment Fix (Codex Review iteration 2)

- `cloudApi.ts`: `UserInfo`, `DeviceInfo`, `LoginData` types aligned with `cloud-backend/app/schemas/auth.py`.
  - `UserInfo`: `id`, `account`, `plan_code` (removed: nickname, avatar_url, plan_id, plan_name)
  - `DeviceInfo`: `id`, `status`, `is_new` (removed: fingerprint, name, is_active, bound_at)
  - `LoginData`: added `expires_in`
- `authStore.ts`: `userName` computed uses `account` only (`nickname` removed).
- `LoginPage.vue`: device display uses `id` + `status` + `is_new` (replaced `device.name`).
- `tasks/current-task.md`: removed `npm test` example (no test script exists).

### Manual Verification Attempt (iteration 2)

**Blocked** — attempted to start cloud backend for live testing:
- PostgreSQL not installed in this environment (`psql` not found, PostgreSQL service not installed).
- Cloud backend requires PostgreSQL `ad_assistant_dev` database, Alembic migrations, and `JWT_SECRET_KEY`.
- All 8 manual verification steps remain **未验证**.

**Request to 大哥**: 请确认是否接受"仅 build + 代码级验证"的残余风险，或提供可用的 PostgreSQL/backend 环境以完成手工验证。

### Codex Review Iteration 3 Fixes (2026-06-01)

Two blocking issues identified by Codex:

#### Fix 1: cloudApi.ts logout sends refresh_token body (was missing)

- **`cloudApi.ts`**: `logout()` now accepts `refreshToken: string | null` and sends `{ refresh_token: ... }` in the POST body to `/api/v1/auth/logout`.
  - Before: `logout()` sent no body — backend `.logout_user()` had no refresh_token to revoke the session.
  - After: body includes `refresh_token` so the backend can revoke the session.
- **`authStore.ts`**: `logout()` now passes `refreshToken.value` to `cloudLogout(refreshToken.value)`.

#### Fix 2: OcrPage.vue Mock AI error display uses sanitizeApiError (not raw apiErr.message)

- **`cloudApi.ts`**: Added `sanitizeApiError(err)` — shared error sanitizer extracted from `authStore.ts` private `sanitizeErrorMessage()`. Covers 401 (UNAUTHORIZED/AUTH_REQUIRED), 403 (FORBIDDEN), 422 (VALIDATION_ERROR), NETWORK_ERROR, and more. Includes `looksInternal()` heuristic to filter stack traces and JSON dumps.
- **`authStore.ts`**: Removed private `sanitizeErrorMessage`/`looksInternal`. Now imports and uses `sanitizeApiError` from `cloudApi.ts`.
- **`OcrPage.vue`**: `handleMockAdCopy()` catch block now calls `sanitizeApiError(apiErr)` instead of `apiErr?.message || "Mock AI 请求失败..."`. This covers all error codes (401/403/422/network) with user-friendly Chinese messages.

#### Build Verification (iteration 3)

| Check | Result |
|-------|--------|
| `npm run build` (desktop-app) | ✅ passed — `vue-tsc --noEmit` + `vite build`, 43 modules transformed, 0 errors |
| `git diff --check` | ✅ passed — no whitespace issues |

### Build Verification

| Check | Result |
|-------|--------|
| `npm run build` (desktop-app) | See iteration 1 re-run below |
| `git diff --check` | See iteration 1 re-run below |
| Frontend tests | Skipped — no test runner in `package.json`; new deps not allowed |
| Backend files | ✅ Zero changes |
| Dependency files | ✅ Zero changes |
| Tauri/local-service | ✅ Zero changes |

### Security Confirmation

- ✅ Tokens memory-only (JavaScript Pinia reactive state — never persisted)
- ✅ No secrets logged
- ✅ No API keys on client
- ✅ Server is sole authority for auth/plan/feature/provider/model/cost/credits
- ✅ Mock-only status clearly labeled in UI
- ✅ Error messages sanitized (Chinese user-friendly, no stack traces)

### Residual Risks

- Login UI is MVP-level; not production account workflow
- Persistent secure token storage deferred
- Mock API response shape may change
- No frontend automated test coverage
