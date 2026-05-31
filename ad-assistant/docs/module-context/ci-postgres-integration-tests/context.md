# CI PostgreSQL Integration Tests Context

## Purpose

This context records the handoff state for the infra task that adds GitHub Actions PostgreSQL service-container coverage for backend migration integration tests.

Future work that modifies this CI workflow must read this file before reading the task sheet and workflow YAML.

## Current State

- Task source: follow-up after Sprint-02 Task-02 credit ledger.
- Current verified `main`: `fc1c271` (`Merge pull request #10 from hohxil84-sketch/feature/sprint-02-task-02-credit-ledger`).
- Task sheet: `tasks/current-task.md`.
- Planning branch used by Codex: `ci-postgres-integration-tests`.
- Proposed implementation branch: `chore/ci-postgres-integration-tests` or `ci-postgres-integration-tests` if slash-style refs are unavailable locally.

## Problem

PostgreSQL integration tests require `TEST_DATABASE_URL`. A developer-local Docker PostgreSQL instance on `localhost:5433` is not reachable from Codex or GitHub Actions because `localhost` is environment-local.

Task-02 PG tests passed on the user's local machine with Docker `postgres:16`, but Codex could not reproduce that run in its own environment.

## Intended Scope

Allowed implementation scope:

- Add `.github/workflows/postgres-integration-tests.yml` (relative to Git repo root `D:/Project`, NOT under `ad-assistant/`).
- Configure PostgreSQL service health check with `pg_isready` (hard requirement to prevent race-condition CI failures).
- Run existing `cloud-backend/tests/test_migrations_integration.py` against a GitHub Actions PostgreSQL service container.
- Document CI and local PG behavior.
- Update this context with implementation facts and test evidence.

Forbidden implementation scope:

- No application code changes.
- No DDL changes.
- No provider/auth/device/usage/credit runtime logic changes.
- No dependency changes.
- No production or staging database connection.
- No repository secret dependency for the test PostgreSQL database.

## Required CI Behavior

- Use `postgres:16`.
- Use temporary credentials such as `postgres` / `test`.
- Configure PostgreSQL service health check (hard requirement):
  use `pg_isready` options (e.g. `pg_isready -U postgres -d postgres`)
  so CI waits for the database to accept connections.
- Set `TEST_DATABASE_URL` to:

```text
postgresql+asyncpg://postgres:test@localhost:5432/postgres
```

- Run:

```bash
cd ad-assistant/cloud-backend
pytest tests/test_migrations_integration.py -v
```

## Implementation Evidence (2026-05-31)

- **Implementation branch**: `ci-postgres-integration-tests`
- **Head commit**: `9860946` (`fix(ci): harden postgres health check and dependency install`)
- **Workflow file**: `.github/workflows/postgres-integration-tests.yml` (at Git repo root `D:/Project`)
- **Changed files**:
  - `.github/workflows/postgres-integration-tests.yml` (new)
  - `docs/21-ci-postgres-integration-tests.md`
  - `docs/module-context/ci-postgres-integration-tests/context.md`
  - `docs/module-context/sprint-02-task-02-credit-ledger/context.md` (CI follow-up fact)
  - `tasks/current-task.md`
- **Exact TEST_DATABASE_URL in CI**: `postgresql+asyncpg://postgres:test@localhost:5432/postgres`
- **Test command**: `cd ad-assistant/cloud-backend && pytest tests/test_migrations_integration.py -v`
- **CI status**: ✅ passed
- **PR**: [#11](https://github.com/hohxil84-sketch/tuwen/pull/11)
- **PR #11 pull_request run**: `26715540044`
- **PR #11 push run**: `26715539485`
- **Test result**: `55 passed, 1 warning in 1.87s`
- **Local static check**: `git diff --check` passed
- **PG service health check**: `pg_isready -U postgres -d postgres` configured with 10s interval, 5s timeout, 5 retries
- **Residual risks**:
  - First CI run surfaced editable-install issue; fixed by switching to explicit
    `pip install` of individual deps from `pyproject.toml` (no `pip install -e`)
  - Future optimization: pip dependency caching for faster CI runs
  - AsyncPG connection to service container `localhost:5432` relies on GitHub Actions default network; if GitHub changes service networking defaults, connection string may need update

## Known Risks

- GitHub Actions may be unavailable or not triggered until the PR is opened.
- Workflow YAML mistakes can create false CI failures.
- The workflow should remain narrow; broader CI matrix work is a separate task.

## Update Rule

Every later change to this CI workflow must update this file with new facts, test results, risks, and follow-up notes.
