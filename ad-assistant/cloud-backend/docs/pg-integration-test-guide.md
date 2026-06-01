# PostgreSQL Integration Test Guide

This guide covers running the DDL integration tests against a real PostgreSQL
instance.  The tests validate that every `cloud-backend/migrations/ddl/*.sql`
file executes correctly — table existence, column types, CHECK/FK constraints,
and downgrade path syntax.

## Quick Start

### 1. Start or install a local test PostgreSQL service

Local development and local test runs must prefer a local PostgreSQL service
over Docker.  If PostgreSQL is not installed locally, install it first through
the OS package manager or the official PostgreSQL installer.  Use Docker only
for CI service containers or when the user explicitly approves Docker as a
fallback.

Create or reuse a temporary local test database, never a production or staging
database.  Example connection string:

```bash
postgresql+asyncpg://postgres:test@localhost:5432/postgres
```

If the local service is not running, start it with the local PostgreSQL service
manager for the machine.

### 2. Run the integration tests

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/test_migrations_integration.py -v
```

### 3. Run **all** tests (SQLite unit + PG integration)

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/ -v
```

### Docker fallback, only when explicitly approved

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:16
until docker exec pg-test pg_isready -U postgres; do sleep 1; done
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/test_migrations_integration.py -v
docker rm -f pg-test
```

## Running Without PostgreSQL (Daily Development)

When `TEST_DATABASE_URL` is **not** set, every integration test is
automatically skipped.  You can always run the full SQLite test suite
without a local PostgreSQL instance:

```bash
cd cloud-backend
pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

Or simply:

```bash
cd cloud-backend
pytest tests/ -v
```

(The integration tests will show as `SKIPPED` in the output.)

## CI Configuration

Add the following step to your CI pipeline **after** the main SQLite test
run:

```yaml
# Example GitHub Actions step
- name: Start PostgreSQL for integration tests
  run: |
    docker run -d --name pg-test \
      -e POSTGRES_PASSWORD=test \
      -p 5432:5432 \
      postgres:16
    until docker exec pg-test pg_isready -U postgres; do sleep 1; done

- name: Run PG integration tests
  env:
    TEST_DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/postgres
  run: |
    cd cloud-backend
    pytest tests/test_migrations_integration.py -v

- name: Clean up
  if: always()
  run: docker rm -f pg-test
```

## What the Tests Cover

| Test class | What it checks |
|------------|---------------|
| `TestTableExistence` | All 6 tables (`users`..`provider_call_log`) are created |
| `TestColumnCompleteness` | Every column exists with the expected data type |
| `TestCheckConstraintNames` | Named CHECK constraints are registered in `pg_constraint` |
| `TestCheckConstraintEnforcement` | Invalid data is rejected with the correct constraint name |
| `TestForeignKeyConstraints` | Non-existent `user_id`/`device_id` references are rejected |
| `TestDowngradePath` | Each DDL file contains a valid `DROP TABLE IF EXISTS` comment |

## Troubleshooting

### `TEST_DATABASE_URL not set` — all tests skipped

Set the environment variable pointing to a running PostgreSQL instance:

```bash
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres
```

### `could not translate host name` / connection refused

Make sure the local PostgreSQL service is running and the port is correct.
If you are using the explicitly approved Docker fallback, check the container:

```bash
docker ps --filter name=pg-test
docker exec pg-test pg_isready -U postgres
```

### Permission denied on Docker

Local development should not default to Docker.  Prefer installing and starting
the local PostgreSQL service.  If the user explicitly approved Docker fallback,
on Linux you may need to add your user to the `docker` group or use `sudo`:

```bash
sudo docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
```

### Test database already contains tables

The session fixture drops all tables on teardown.  If a previous run crashed
mid-test, you can manually clean up:

```bash
psql -d postgres -c "DROP TABLE IF EXISTS provider_call_log, usage_events, risk_logs, auth_sessions, devices, users CASCADE;"
```

If using the explicitly approved Docker fallback, you can recreate the
container:

```bash
docker rm -f pg-test
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
```
