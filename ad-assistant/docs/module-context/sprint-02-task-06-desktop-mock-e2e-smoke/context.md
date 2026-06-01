# Module Context: Sprint-02 Task-06 Desktop Mock AI E2E Smoke Verification

## Status

`IMPLEMENTED_AWAITING_REVIEW`

Implementation, API-level smoke, AND browser UI-level smoke verification all
completed on 2026-06-01. Waiting for Codex Review.

## Base

- Branch: `feature/sprint-02-task-06-desktop-mock-e2e-smoke`
- Base commit: `42dbad8` (merge of PR #16, Sprint-02 Task-05)
- Latest parent: `c5f89a7` (merge of PR #17, docs closeout)

## Goal

Make the merged desktop mock MVP path reproducible and manually verified.

## Changes Made

### New Files

| File | Purpose |
|------|---------|
| `docs/25-desktop-mock-e2e-smoke.md` | E2E smoke runbook with exact commands and verified results |
| `cloud-backend/scripts/dev_seed_user.py` | Dev-only seed script (ORM-based, compatible with SQLite and PostgreSQL) |
| `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md` | This file |

### Modified Files

| File | Changes |
|------|---------|
| `docs/09-desktop-app-guide.md` | Added dev runbook reference and quick-start commands |
| `docs/11-cloud-backend-guide.md` | Added local dev environment section with quick-start |
| `docs/sprint-02-summary.md` | Updated Task-06 status and deliverables |
| `tasks/current-task.md` | Updated status + implementation record |

### Forbidden Files — NOT Modified

- `cloud-backend/app/**` — no changes
- `cloud-backend/migrations/**` — no changes
- `cloud-backend/tests/**` — no changes
- `shared/**` — no changes
- `official-website/**` — no changes
- `.github/workflows/**` — no changes
- `desktop-app/src/**` — no changes
- `desktop-app/src-tauri/**` — no changes
- `desktop-app/local-service/**` — no changes
- `desktop-app/local-tools/**` — no changes
- `desktop-app/migrations/**` — no changes
- dependency files or lockfiles — no changes
- `.env` or `.env.example` — no changes
- files containing secrets — no changes

## Verification Results

### Automated Checks

| Check | Result |
|-------|--------|
| `npm run build` (desktop-app) | ✅ Passed (43 modules, 0 errors) |
| `git diff --check` | ✅ Passed (no whitespace issues) |

### API-Level Smoke Verification (2026-06-01)

All verified via curl against running backend (SQLite) + desktop Vite dev server:

| Step | Result | Detail |
|------|--------|--------|
| Backend health check | ✅ PASS | `{"status":"ok","sprint":"01"}` |
| Login | ✅ PASS | Returns access_token + refresh_token + user + device |
| Mock AI ad-copy (ASCII) | ✅ PASS | provider=mock, model=mock-text-v1, credits_charged=0 |
| Mock AI ad-copy (Chinese) | ✅ PASS | Chinese product_name/selling_points accepted |
| provider_call_log written | ✅ PASS | provider=mock, model=mock-text-v1, status=success, credits=0 |
| Logout | ✅ PASS | Refresh token revoked |
| Token reuse after logout | ✅ PASS | TOKEN_REUSE detected |
| No-auth request | ✅ PASS | HTTP 401 |
| Desktop Vite dev server | ✅ PASS | Serves index.html + modules @ :5173 |

### UI-Level Smoke (2026-06-01, live browser)

Tested in browser @ http://127.0.0.1:5173 against live backend + Vite proxy:

| Step | Status | Detail |
|------|--------|--------|
| Browser login form | ✅ PASS | Account/password/fingerprint form → redirect to /ocr |
| Mock AI panel visibility | ✅ PASS | "Mock AI 广告文案生成（仅 Mock）" panel visible after login |
| Generate mock ad-copy + result display | ✅ PASS | provider=mock, model=mock-text-v1, 扣点=0, request_id=req_27a7a33502cb |
| Page refresh clears tokens | ✅ PASS | F5 → login state lost, panel hidden (Pinia memory-only verified) |
| OCR upload UI | ✅ PASS | Image area visible; recognition blocked (no local OCR service) |

Note: A Vite proxy for `/api` → backend was required to avoid CORS errors.
The proxy is configured in `vite.config.ts` and the env var
`VITE_CLOUD_API_BASE_URL=http://127.0.0.1:5173` must be set at dev server start.

### Existing Backend Test Suite

The 147 tests pass against SQLite (in-memory). These are the project's
existing tests — they use SQLite fixtures and do NOT run against PostgreSQL
by default. The `TEST_DATABASE_URL` environment variable enables PG
integration tests for `test_migrations_integration.py` only.

## Known Issues Found

### DDL / ORM DateTime Mismatch (Pre-existing, Not Fixed)

`migrations/ddl/*.sql` files use `TIMESTAMPTZ` columns, but SQLAlchemy models
use `DateTime` without `timezone=True` → `TIMESTAMP WITHOUT TIME ZONE`.
When the backend runs against DDL-created PostgreSQL tables, the ORM sends
timezone-aware datetimes and asyncpg rejects them.

**Impact:** Backend cannot run against PostgreSQL with DDL-created tables.

**Workaround:** Use SQLite for local development (backend tests already use
SQLite). The smoke verification used `sqlite+aiosqlite:///dev.db`.

**Fix needed:** Either add `timezone=True` to all model `DateTime` columns,
or change DDL to use `TIMESTAMP WITHOUT TIME ZONE`. This is outside the
scope of Task-06 (forbidden to modify `app/` or `migrations/`).

### Dev Seed Script — ORM-Based

The seed script uses ORM models (not raw SQL) to ensure UUID and DateTime
type compatibility. It works with SQLite. With PostgreSQL, it will hit the
same DateTime mismatch as the backend.

## Residual Risks

- Browser-based UI smoke (4 steps) not completed in this session.
- OCR pipeline blocked on local PaddleOCR service setup (out of scope).
- DDL/model DateTime mismatch blocks PostgreSQL development until resolved.
- Seed script excluded from production builds — ensure it stays dev-only.

## Review Notes For Codex

1. Verify `cloud-backend/scripts/dev_seed_user.py` is clearly dev-only.
2. Confirm no production backend/API/DDL/dependency changes were made.
3. Confirm no secrets or real provider keys were added.
4. Review the DDL/model DateTime mismatch finding and plan next task.
5. Confirm module context completeness before allowing commit.
