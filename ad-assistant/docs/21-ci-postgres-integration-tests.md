# CI PostgreSQL Integration Tests

## Purpose

This document describes the planned CI path for PostgreSQL migration integration tests.

The project already has real PostgreSQL tests in `cloud-backend/tests/test_migrations_integration.py`. Those tests require `TEST_DATABASE_URL`. When the variable is absent, the tests skip so normal local SQLite development is not blocked.

## Problem

A developer can run PostgreSQL locally with Docker, for example on `localhost:5433`. Codex and GitHub Actions do not share that developer-machine network namespace. For them, `localhost` means their own execution environment, not the developer's computer.

Therefore, a URL like this is valid only on the machine where Docker is running:

```text
postgresql+asyncpg://postgres:test@localhost:5433/postgres
```

CI must start its own PostgreSQL service container and point `TEST_DATABASE_URL` at that CI-local service.

## Implemented CI Behavior

The workflow file `.github/workflows/postgres-integration-tests.yml` (at Git repo root `D:/Project`) implements the following CI contract:

- run on PRs targeting `main`;
- run on pushes to `ci-postgres-integration-tests` and `chore/ci-postgres-integration-tests`;
- use `ubuntu-latest`;
- use `ubuntu-latest`;
- use Python 3.12;
- start PostgreSQL with `postgres:16`;
- configure a `pg_isready` health check so CI waits for the database
  to accept connections before running tests (race condition avoidance);
- use temporary test credentials only;
- install existing backend dev dependencies;
- run the PostgreSQL integration suite.

CI connection string:

```text
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres
```

Primary CI command:

```bash
cd ad-assistant/cloud-backend
pytest tests/test_migrations_integration.py -v
```

## Local Behavior

Developers can still run the same suite manually against local Docker:

```powershell
cd cloud-backend
$env:TEST_DATABASE_URL='postgresql+asyncpg://postgres:test@localhost:5433/postgres'
pytest tests/test_migrations_integration.py -v
```

The local port may differ. The important rule is that the database must be a temporary test PostgreSQL instance, never production.

## Security Rules

- Do not use production or staging database URLs.
- Do not require repository secrets for the test database.
- Do not store real credentials in workflow YAML.
- Use only ephemeral CI service container credentials.
- Keep application runtime behavior unchanged.

## Scope Boundaries

This infra task may add a workflow under `.github/workflows/` (relative to the Git repository root `D:/Project`, NOT under `ad-assistant/`), but must not change:

- database DDL files;
- application services or routes;
- provider logic;
- auth or device logic;
- credit runtime logic;
- shared DTO or OpenAPI files;
- frontend or desktop code;
- dependency files.

## Success Criteria

The PR should show GitHub Actions running `tests/test_migrations_integration.py` against PostgreSQL `postgres:16` and passing without any developer-local Docker dependency.

## Implementation Evidence

- **Workflow file**: `.github/workflows/postgres-integration-tests.yml` (repo root `D:/Project`)
- **Branch**: `ci-postgres-integration-tests`
- **CI status**: pending PR open to `main` to observe GitHub Actions execution
- **Local static checks**: `git diff --check` passed
