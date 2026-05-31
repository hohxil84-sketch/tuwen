# Module Context: Sprint-02 Task-05 Desktop Mock AI API Client

## Status

`MERGED` — implementation complete on 2026-06-01, Codex approved on 2026-06-01, merged to `main` by PR #16.

Merge evidence:
- Feature commit: `89b901a feat(desktop): add mock AI cloud API client (Sprint-02 Task-05)`
- Merge commit: `42dbad8 Merge pull request #16 from hohxil84-sketch/feature/sprint-02-task-05-desktop-mock-ai-client`
- Merge strategy: merge commit, no squash, no rebase.
- Base before merge: `645d181 docs(closeout): record Sprint-02 Task-04 completion (#15)`
- PR #16 CI: `pg-integration` passed.

Codex Review iteration 1 fixes applied on 2026-06-01:
- request_id now flows from cloudApi response envelope → authStore → OcrPage (no placeholder text).
- Router comment corrected to reflect no guard was added.
- tasks/current-task.md restored to full task sheet structure with implementation evidence appended.

Codex Review iteration 2 fixes applied on 2026-06-01:
- cloudApi.ts types aligned with backend auth.py: UserInfo (id, account, plan_code), DeviceInfo (id, status, is_new), LoginData (+expires_in).
- authStore.ts userName uses account only (nickname removed).
- LoginPage.vue device display uses id + status + is_new (fingerprint/name removed).
- tasks/current-task.md npm test example removed (no test script exists).

Codex Review iteration 3 fixes applied on 2026-06-01:
- cloudApi.ts logout() now sends refresh_token in body → backend can revoke session.
- authStore.ts logout() passes refreshToken.value to cloudLogout().
- cloudApi.ts: extracted sanitizeApiError() as shared error sanitizer (maps codes → CN user messages, filters internal data).
- authStore.ts: removed private sanitizeErrorMessage/looksInternal; imports sanitizeApiError.
- OcrPage.vue: Mock AI errors now routed through sanitizeApiError (was raw apiErr.message).

## Branch

- `feature/sprint-02-task-05-desktop-mock-ai-client`
- Based on `main` @ `8fa3440`
- Merged to `main` @ `42dbad8`

## Goal

Connect the desktop app to the protected cloud mock AI endpoint:

```text
POST /api/v1/mock-ai/ad-copy
```

## Implementation Summary

### New Files

| File | Purpose |
|------|---------|
| `desktop-app/src/services/cloudApi.ts` | Typed cloud API HTTP client |
| `desktop-app/src/stores/authStore.ts` | Pinia store — in-memory auth/session |
| `docs/24-desktop-mock-ai-api-client.md` | Task implementation doc |

### Modified Files

| File | Changes |
|------|---------|
| `desktop-app/src/pages/LoginPage.vue` | Full login form → cloud auth → redirect to /ocr |
| `desktop-app/src/pages/OcrPage.vue` | Added Mock AI ad-copy panel (below OCR area, login-gated) |
| `desktop-app/src/router.ts` | Unchanged structure (hash router unchanged) |
| `desktop-app/src/App.vue` | Added navigation header with links + auth state |
| `desktop-app/src/env.d.ts` | Added `VITE_CLOUD_API_BASE_URL` type to `ImportMetaEnv` |
| `docs/09-desktop-app-guide.md` | Updated with cloud API client info |
| `docs/sprint-02-summary.md` | Updated task status |
| `tasks/current-task.md` | Updated status to IMPLEMENTING → IMPLEMENTED |

## Key Design Decisions

1. **No Pinia getter for auth in router guard**: The hash router does not support async navigation guards simply with Pinia outside component context. Instead, each page reacts to `auth.isLoggedIn` — the OCR page shows a login prompt when not authenticated.
2. **`import.meta.env` for base URL**: Uses Vite's built-in env mechanism with a typed `ImportMetaEnv` interface.
3. **Error sanitization in cloudApi.ts** (iteration 3): `sanitizeApiError()` is a shared, exported function that maps backend error codes to Chinese user-facing messages and filters internal-looking messages. Used by both `authStore.ts` (login errors) and `OcrPage.vue` (Mock AI errors).
4. **No test framework**: `package.json` has no vitest/jest. Per task rules, no new dependencies were added.

## Verification

### Automated

- `npm run build`: ✅ 43 modules, 0 errors (2026-06-01, re-verified iteration 3)
- `git diff --check`: ✅ no whitespace issues
- PR #16 `pg-integration`: ✅ passed
- No backend files touched
- No dependency files touched
- No Tauri/local-service/shared changes

### Manual (2026-06-01, iteration 2)

**Attempted to start cloud backend for manual verification — blocked:**
- PostgreSQL not installed in this environment (psql not found, service not installed).
- Cloud backend requires PostgreSQL `ad_assistant_dev` database, migrations, and JWT_SECRET_KEY.
- Without a running backend, login and mock ad-copy tests cannot be performed.

All manual verification steps remain **未验证**:

1. Cloud backend: 未验证 (not started)
2. Desktop dev server: 未验证 (only production build ran)
3. Login: 未验证 (depends on backend)
4. Mock AI panel visibility: 未验证 (depends on login)
5. Mock ad-copy request/response: 未验证 (depends on backend)
6. UI fields (provider=mock, model=mock-text-v1, credits_charged=0, real request_id): 未验证
7. Token cleared on refresh: 未验证 (depends on login)
8. OCR workflow intact: 未验证 (depends on local OCR service)

### Code-level verification performed

- TypeScript compilation passes (vue-tsc --noEmit + vite build)
- Full request_id pipeline: `cloudApi.ts` → `authStore.ts` → `OcrPage.vue` unified through `MockAdCopyResponse` type
- All files within allowed scope; no forbidden files modified

## Security Boundaries (verified)

- ✅ Tokens memory-only (no localStorage, sessionStorage, IndexedDB, SQLite, cookies, files, Tauri storage)
- ✅ No API keys sent to client
- ✅ Client does not decide provider/model/plan/feature/cost/credits
- ✅ No third-party AI API calls from desktop
- ✅ UI labels output as Mock/测试

## Known Risks

- Login UI is MVP-level; not a production account workflow
- Persistent secure token storage deferred
- Mock API response shape may change
- No frontend automated test coverage (test runner not available)

## Next Steps (after Codex Review)

- Task-05 is merged; do not continue development on the Task-05 branch.
- Codex prepared Sprint-02 Task-06 draft in `tasks/current-task.md`.
- Next implementation must wait for user confirmation and use a new task branch.
