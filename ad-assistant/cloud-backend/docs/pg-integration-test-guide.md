# PostgreSQL Integration Test Guide

This guide covers running the DDL integration tests against a real PostgreSQL
instance.  The tests validate that every `cloud-backend/migrations/ddl/*.sql`
file executes correctly — table existence, column types, CHECK/FK constraints,
and downgrade path syntax.

## Quick Start

### 1. Start a local test PostgreSQL container

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:16
```

### 2. Wait for PostgreSQL to be ready

```bash
until docker exec pg-test pg_isready -U postgres; do sleep 1; done
```

### 3. Run the integration tests

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/test_migrations_integration.py -v
```

### 4. Run **all** tests (SQLite unit + PG integration)

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/ -v
```

### 5. Tear down the container when done

```bash
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

Make sure the Docker container is running and the port is correct:

```bash
docker ps --filter name=pg-test
docker exec pg-test pg_isready -U postgres
```

### Permission denied on Docker

On Linux you may need to add your user to the `docker` group or use `sudo`:

```bash
sudo docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
```

### Test database already contains tables

The session fixture drops all tables on teardown.  If a previous run crashed
mid-test, you can manually clean up:

```bash
docker exec pg-test psql -U postgres -c "DROP TABLE IF EXISTS provider_call_log, usage_events, risk_logs, auth_sessions, devices, users CASCADE;"
```

Or simply recreate the container:

```bash
docker rm -f pg-test
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
```
