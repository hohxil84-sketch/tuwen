# Sprint-02 Task-02 Credit Ledger Context

## Purpose

This context records the handoff state for Sprint-02 Task-02: AI credit account and ledger foundation.

Future work that extends or modifies this module must read this file before reading the task sheet and code.

## Current State

- Current verified local `main`/`HEAD` at review start: `bdf08ed` (`Merge pull request #9 from hohxil84-sketch/docs/module-context-rule`)
- Earlier task-sheet merge note: `da3b31e`
- Task sheet PR: `#8`
- Task sheet branch: `docs/sprint-02-task-02-credit-ledger`
- Implementation branch: `feature/sprint-02-task-02-credit-ledger`
- Current task sheet: `tasks/current-task.md`

## Task Scope

Task-02 is approved only after the user explicitly confirms the major-change task sheet.

Allowed implementation scope:

- Add `credit_accounts` and `credit_ledger` DDL as `007` and `008`.
- Add ORM models, schema, credit service, and read-only Credit API.
- Add SQLite tests and extend PostgreSQL migration integration tests.
- Update `cloud-backend/tests/conftest_pg.py` only so the PG fixture expects and applies DDL `001` through `008`.
- Update `docs/05-api-contract.md` only for current Credit API behavior.

Forbidden implementation scope:

- No real AI Provider call.
- No real credit deduction.
- No recharge, payment, order, plan purchase, or grant automation.
- No admin console.
- No frontend, desktop, Tauri, shared OpenAPI, DTO, or TypeScript changes.
- No edits to existing DDL files `001` through `006`.
- No provider_call_log field changes.
- No dependency or lockfile changes.

## Required Tests

SQLite path:

```bash
cd cloud-backend
pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

PostgreSQL path:

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres \
  pytest tests/test_migrations_integration.py -v
```

The PostgreSQL port may differ on a developer machine. If it differs, record the actual local test URL in the completion output. Never use a production database.

Static checks:

```bash
cd D:/Project/ad-assistant
git status --short --branch
git diff --check
```

## Known Decisions

- `credit_accounts` starts with zero balance on first query; this task does not auto-grant monthly credits.
- Credit APIs are read-only from the client perspective.
- `record_credit_ledger(...)` may exist as an internal service helper, but no public write API is allowed in this task.
- This task is a major change because it adds schema, API, and credit service logic. The task sheet is the major-change proposal.
- PG fixture coverage must grow from six to eight DDL files for this task; this is test infrastructure only and does not change production runtime behavior.

## 2026-05-31 Review Notes

Changed files observed on `feature/sprint-02-task-02-credit-ledger`:

- `cloud-backend/migrations/ddl/007_credit_accounts.sql`
- `cloud-backend/migrations/ddl/008_credit_ledger.sql`
- `cloud-backend/app/models/credit_account.py`
- `cloud-backend/app/models/credit_ledger.py`
- `cloud-backend/app/models/__init__.py`
- `cloud-backend/app/schemas/credit.py`
- `cloud-backend/app/services/credit_service.py`
- `cloud-backend/app/api/v1/credits.py`
- `cloud-backend/app/main.py`
- `cloud-backend/tests/test_credit.py`
- `cloud-backend/tests/test_migrations_integration.py`
- `cloud-backend/tests/conftest_pg.py`
- `docs/05-api-contract.md`
- `tasks/current-task.md`
- `docs/module-context/sprint-02-task-02-credit-ledger/context.md`

Test results:

- `pytest tests/ -v --ignore=tests/test_migrations_integration.py` in `cloud-backend`: `102 passed, 1 warning in 12.78s`.
- `git diff --check` in repo root: passed.
- PostgreSQL integration test was executed on the user's local machine, not in the Codex environment, because Codex could not reach the user's local Docker `localhost:5433`.
- User-provided PostgreSQL evidence:
  - command: `$env:TEST_DATABASE_URL='postgresql+asyncpg://postgres:test@localhost:5433/postgres'; pytest tests/test_migrations_integration.py -v`
  - actual URL: `postgresql+asyncpg://postgres:test@localhost:5433/postgres`
  - database: local Docker `postgres:16` mapped to port `5433`
  - result: `55 passed in 3.04s`
- Combined evidence for Task-02 review: SQLite/non-PG `102 passed` plus PostgreSQL integration `55 passed`, total `157 passed, 0 failed`.

Known review risks:

- PostgreSQL migration assertions were reviewed from user-provided local execution output rather than reproduced in the Codex environment.
- The task touches confirmed major-change areas: new database schema, read-only Credit API, and credit service logic. No client-write credit API should be added in this task.

## Update Rule

Every later change to this module must update this file with:

- New commit or PR reference.
- Changed files.
- Test results.
- New risks or decisions.
- Follow-up notes for future modifications.
