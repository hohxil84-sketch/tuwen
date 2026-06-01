# Module Context: Sprint-02 Task-07 Backend PostgreSQL DateTime Alignment

## Status

`IMPLEMENTED_AWAITING_REVIEW`

Implementation completed on 2026-06-01. Waiting for Codex Review.

## Base

- Branch: `feature/sprint-02-task-07-pg-datetime-align`
- Base: `main` @ `afd1ca4` (PR #19 merge — docs: clarify Vite proxy API base URL)

## Goal

Align SQLAlchemy models `DateTime` column type declarations with DDL `TIMESTAMPTZ`,
resolving the pre-existing ORM/DDL mismatch discovered during Task-06 E2E smoke.

## Pre-Existing Problem (from Task-06)

- DDL: `TIMESTAMPTZ` (PostgreSQL best practice)
- ORM: `DateTime` without `timezone=True` → `TIMESTAMP WITHOUT TIME ZONE`
- Conflict: asyncpg rejected timezone-aware datetimes against mismatched columns

## Fix Applied

Added `DateTime(timezone=True)` to all 18 datetime columns across 8 model files.

| Model File | Columns |
|-----------|----------|
| `app/models/user.py` | `created_at`, `updated_at` |
| `app/models/device.py` | `first_seen_at`, `last_seen_at`, `created_at`, `updated_at` |
| `app/models/auth_session.py` | `expires_at`, `revoked_at`, `created_at`, `updated_at` |
| `app/models/credit_account.py` | `period_start`, `period_end`, `created_at`, `updated_at` |
| `app/models/credit_ledger.py` | `created_at` |
| `app/models/provider_call_log.py` | `created_at` |
| `app/models/risk_log.py` | `created_at` |
| `app/models/usage_event.py` | `created_at` |

## Changed Files

### Models (core fix)

- `cloud-backend/app/models/user.py`
- `cloud-backend/app/models/device.py`
- `cloud-backend/app/models/auth_session.py`
- `cloud-backend/app/models/credit_account.py`
- `cloud-backend/app/models/credit_ledger.py`
- `cloud-backend/app/models/provider_call_log.py`
- `cloud-backend/app/models/risk_log.py`
- `cloud-backend/app/models/usage_event.py`

### Seed Script

- `cloud-backend/scripts/dev_seed_user.py` — docstring updated (mismatch resolved)

### Documentation

- `docs/25-desktop-mock-e2e-smoke.md` — removed PG bypass note, added PG alternative section
- `docs/11-cloud-backend-guide.md` — updated PG status from "blocked" to "supported"
- `docs/12-database-design.md` — added timestamp alignment note
- `docs/sprint-02-summary.md` — added Task-07 status
- `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md` — this file

### Forbidden Files — NOT Modified

- `cloud-backend/migrations/ddl/*.sql` — DDL unchanged (TIMESTAMPTZ is correct)
- `cloud-backend/migrations/migration-plan-draft.md`
- `cloud-backend/app/api/**` — no changes
- `cloud-backend/app/services/**` — no changes
- `cloud-backend/app/core/**` — no changes
- `cloud-backend/app/providers/**` — no changes
- `cloud-backend/app/schemas/**` — no changes
- `cloud-backend/tests/**` — no changes (tests passed without modification)
- `shared/**` — no changes
- `desktop-app/**` — no changes
- `official-website/**` — no changes
- `.github/workflows/**` — no changes
- dependency files — no changes

## Verification Results

| Check | Result |
|-------|--------|
| SQLite regression (147 tests) | ✅ 147 passed |
| PG DDL integration (55 tests) | ✅ 55 passed |
| ORM `create_all` against PG | ✅ succeeded |
| `dev_seed_user.py` against PG | ✅ user created + device bound |
| `git diff --check` | ✅ passed |

## Known Risks

- Services code (`app/services/`, `app/api/`) was not modified but should be reviewed
  for any datetime comparison/formatting logic that may rely on naive datetime assumptions.
- The grep check of services/api datetime usage found no obvious issues, but full
  integration testing against PostgreSQL (backend running + API calls) was not in scope.

## Residual Risks

- Full backend integration smoke against PostgreSQL (start backend, login, mock AI call)
  was not repeated for this task — covered by Task-06 runbook's new PG alternative section.
- No new test files were created; existing tests cover the ORM type change adequately.

## Major Change Status

**Yes — major change.** Model column type declarations modified. User confirmed 2026-06-01.
DDL, API contracts, physical schema, dependencies unchanged.

## Review Notes For Codex

1. Verify only model files + docs were changed.
2. Confirm no DDL, API, service, provider, shared, desktop, or dependency changes.
3. Confirm test results: SQLite 147, PG 55, ORM read/write.
4. Confirm this is within the user-confirmed major change scope.
5. Allow commit if all checks pass.
