# 24 — Desktop Mock AI API Client (Sprint-02 Task-05)

Date: 2026-06-01
Branch: `feature/sprint-02-task-05-desktop-mock-ai-client`
Base: `main` @ `8fa3440`
Status: `IMPLEMENTED_AWAITING_CODEX_REVIEW` (iteration 2 fixes applied)

## Purpose

Connect the desktop app to the protected cloud Mock AI endpoint:

```text
POST /api/v1/mock-ai/ad-copy
```

This is a desktop integration slice only — no real AI, no real billing, no token persistence.

## What Was Built

### New Files

| File | Purpose |
|------|---------|
| `desktop-app/src/services/cloudApi.ts` | Typed cloud API HTTP client for login/logout/mock-ai |
| `desktop-app/src/stores/authStore.ts` | Pinia store — in-memory auth/session state |

### Modified Files

| File | Changes |
|------|---------|
| `desktop-app/src/pages/LoginPage.vue` | Account/password/device-fingerprint login form → cloud auth |
| `desktop-app/src/pages/OcrPage.vue` | Mock AI ad-copy panel below OCR (login-gated, mock-labeled) |
| `desktop-app/src/router.ts` | No structural changes |
| `desktop-app/src/App.vue` | Navigation header with links + auth state |
| `desktop-app/src/env.d.ts` | Added `VITE_CLOUD_API_BASE_URL` type |

### Key Behaviors

- Login sends account, password, device fingerprint to `POST /api/v1/auth/login`.
- Tokens stored in JavaScript memory only (Pinia reactive state).
- `POST /api/v1/mock-ai/ad-copy` sends only `product_name`, `selling_points`, `platform`, `tone`.
- Client never sends provider, model, cost, credits, user_id, device_id, plan, or permission decisions.
- Mock result UI shows: provider, model, credits_charged (0), request_id, generated text.
- Mock-only badge and notice visible in the UI.
- Error messages are sanitized (Chinese user-friendly; no stack traces, no raw JSON).

### Codex Review Iteration 2 — Type Alignment (2026-06-01)

- **cloudApi.ts**: `UserInfo`, `DeviceInfo`, `LoginData` types aligned with `cloud-backend/app/schemas/auth.py`.
  - `UserInfo`: `id`, `account`, `plan_code` (removed: nickname, avatar_url, plan_id, plan_name).
  - `DeviceInfo`: `id`, `status`, `is_new` (removed: fingerprint, name, is_active, bound_at).
  - `LoginData`: added `expires_in`.
- **authStore.ts**: `userName` computed uses `account` only (no more `nickname` fallback).
- **LoginPage.vue**: device display uses `id` + `status` + `is_new` (replaced `device.name`).
- **tasks/current-task.md**: removed `npm test` example (no test script in package.json).
- `npm run build` + `git diff --check` ✅ passed (0 type errors, 43 modules).

## Security

- ✅ Tokens are memory-only — never persisted to localStorage, sessionStorage, IndexedDB, SQLite, cookies, files, or Tauri storage.
- ✅ Passwords, device fingerprints, and request bodies are never logged.
- ✅ No API keys ever sent to the client.
- ✅ Server is the sole authority for auth/plan/feature/provider/model/cost/credits.
- ✅ No third-party AI API calls from the desktop app.
- ✅ Mock-only status clearly labeled in the UI.

## Verification

### Automated Checks

| Check | Result |
|-------|--------|
| `npm run build` (desktop-app) | ✅ Passed (43 modules, 0 errors, 2026-06-01) |
| `git diff --check` | ✅ Passed |
| Frontend automated tests | Skipped — no test runner in `package.json`; new deps not allowed per task rules |
| Backend files touched | ✅ None |
| Dependency changes | ✅ None |
| Tauri/local-service/shared changes | ✅ None |

### Manual Verification Results (2026-06-01, iteration 2)

**Attempted to start cloud backend — blocked:**
- PostgreSQL is not installed in this environment.
- Cloud backend requires PostgreSQL `ad_assistant_dev` database + migrations + JWT_SECRET_KEY.
- Without backend, login and mock ad-copy cannot be tested against a live server.

Manual verification steps:

| Step | Description | Result | Notes |
|------|-------------|--------|-------|
| 1 | Cloud backend started at `http://127.0.0.1:8000` | ❌ 未验证 | No cloud backend instance was running in this session. Requires a local cloud backend with test DB and seed data. |
| 2 | Desktop Vite dev server started | ❌ 未验证 | Dev server was not started; only `npm run build` (production build) was executed. The build artifact was generated correctly. |
| 3 | Login with test account and device fingerprint | ❌ 未验证 | Depends on steps 1 and 2. Login form is implemented but not tested against a live backend. |
| 4 | "Mock AI 广告文案生成" panel visible after login | ❌ 未验证 | Depends on step 3. Panel is implemented with `v-if="auth.isLoggedIn"` guard. |
| 5 | Mock ad-copy request submitted and response received | ❌ 未验证 | Depends on steps 1-3. Full request/response pipeline is implemented. |
| 6 | UI displays provider=mock, model=mock-text-v1, credits_charged=0, real request_id | ❌ 未验证 | Depends on step 5. The `MockAdCopyResponse` type includes `request_id` from the backend envelope. No placeholder text is used. |
| 7 | Page refresh clears token state | ❌ 未验证 | Depends on step 3. Tokens are stored in Pinia reactive state (in-memory); refresh inherently clears them. |
| 8 | Existing OCR upload/recognition/history not broken | ❌ 未验证 | OCR page was not tested against a live local OCR service. Existing OCR code paths (upload, preview, OCR trigger, result display, file validation) were preserved in the template and script. The mock AI panel is an additive section below the existing OCR result area. |

### Summary

- **Automated checks**: All passed (`npm run build`, `git diff --check`).
- **Manual verification**: All 8 manual steps are **未验证** because no cloud backend or local OCR service was running in this build session.
- **Code-level verification performed**: TypeScript compilation passes (vue-tsc --noEmit + vite build); the full request_id pipeline from `cloudApi.ts` → `authStore.ts` → `OcrPage.vue` is unified through the `MockAdCopyResponse` type; all files are within the allowed scope; no forbidden files were modified.

## Non-Goals (verified)

- ❌ No backend code changes
- ❌ No DDL or migration changes
- ❌ No Provider/credit/payment changes
- ❌ No real AI provider SDKs, API keys, or network calls
- ❌ No OpenAPI/shared DTO generation
- ❌ No Tauri permission changes
- ❌ No local Python service changes
- ❌ No new dependencies
- ❌ No token persistence
- ❌ No generic prompt UI or provider/model picker

## Residual Risks

- Login UI is MVP-level; not production account workflow.
- Persistent secure token storage deferred to future task.
- Mock API response shape may change in future API-contract tasks.
- No frontend automated test coverage (test runner absent from `package.json`).

## Related Docs

- Task sheet: `tasks/current-task.md`
- Module context: `docs/module-context/sprint-02-task-05-desktop-mock-ai-client/context.md`
- Desktop guide: `docs/09-desktop-app-guide.md`
- Sprint summary: `docs/sprint-02-summary.md`
- Backend endpoint: `docs/23-mock-ai-api-endpoint.md`
