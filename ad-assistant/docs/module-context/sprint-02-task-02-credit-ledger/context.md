# Sprint-02 Task-02 Credit Ledger Context

## Purpose

This context records the handoff state for Sprint-02 Task-02: AI credit account and ledger foundation.

Future work that extends or modifies this module must read this file before reading the task sheet and code.

## Current State

- Main commit after task-sheet merge: `da3b31e`
- Task sheet PR: `#8`
- Task sheet branch: `docs/sprint-02-task-02-credit-ledger`
- Implementation branch to create: `feature/sprint-02-task-02-credit-ledger`
- Current task sheet: `tasks/current-task.md`

## Task Scope

Task-02 is approved only after the user explicitly confirms the major-change task sheet.

Allowed implementation scope:

- Add `credit_accounts` and `credit_ledger` DDL as `007` and `008`.
- Add ORM models, schema, credit service, and read-only Credit API.
- Add SQLite tests and extend PostgreSQL migration integration tests.
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

## Update Rule

Every later change to this module must update this file with:

- New commit or PR reference.
- Changed files.
- Test results.
- New risks or decisions.
- Follow-up notes for future modifications.
