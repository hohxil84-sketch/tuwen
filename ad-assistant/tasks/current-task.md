# Current Task: Infra - GitHub Actions PostgreSQL Integration Tests

## Status

`IMPLEMENTED` — implementation complete on branch `ci-postgres-integration-tests`. Awaiting Codex Review before commit and merge.

## Suggested Branch

`chore/ci-postgres-integration-tests`, based on latest `main`.

If a local Git ref permission or slash-name issue occurs, use the flat branch name `ci-postgres-integration-tests`.

## Prerequisites

- Sprint-02 Task-02 was merged to `main` by PR #10.
- Current verified merge commit: `fc1c271` (`Merge pull request #10 from hohxil84-sketch/feature/sprint-02-task-02-credit-ledger`).
- PostgreSQL migration integration tests already exist in `cloud-backend/tests/test_migrations_integration.py`.
- The PG fixture reads `TEST_DATABASE_URL` in `cloud-backend/tests/conftest_pg.py`.
- Local manual PG evidence for Task-02 was `55 passed` against Docker `postgres:16` on `localhost:5433`.
- Codex could not reproduce that local result because Codex's environment cannot reach a developer-machine Docker service on `localhost:5433`.

## Background

The project now has real PostgreSQL DDL integration tests, but they only run when `TEST_DATABASE_URL` points to a reachable PostgreSQL instance. On developer machines this can be handled with local Docker. In Codex or CI, `localhost:5433` does not refer to the developer machine, so PostgreSQL assertions may be skipped or fail during connection setup.

This task adds CI-owned PostgreSQL infrastructure so GitHub Actions can run the PostgreSQL integration suite in the same network namespace as a temporary PostgreSQL service container.

## Major Change Proposal

This task modifies CI/project infrastructure by adding `.github/workflows/**`. It does not modify application runtime behavior, database schema, API contract, provider logic, auth logic, credit logic, shared DTO, desktop code, or dependencies.

User confirmation is still required before implementation because this introduces a new GitHub Actions workflow and affects PR validation.

1. Reason
   - Remove dependence on a developer's local Docker PostgreSQL instance for PG integration tests.
   - Make `tests/test_migrations_integration.py` run automatically on PRs and pushes.
   - Prevent future DDL tasks from being accepted without a real PostgreSQL execution path.

2. Risks
   - CI runtime may increase.
   - Workflow YAML mistakes can create false red/green CI signals.
   - Service container health checks or connection strings can be flaky if not configured explicitly.
   - CI secrets must not be used for this test database.

3. Impact
   - Adds a GitHub Actions workflow under `.github/workflows/`.
   - Runs existing backend tests against a temporary PostgreSQL service container.
   - Does not change production code or production database behavior.

4. Rollback
   - Delete the new workflow file.
   - No database rollback is needed.
   - No application code rollback is needed.

5. Backward Compatibility
   - Compatible. Existing local test commands remain unchanged.
   - If `TEST_DATABASE_URL` is not set locally, PG tests continue to skip by design.

6. Database Migration
   - None. This task must not add, remove, or edit DDL files.

## What To Build

### 1. Add GitHub Actions workflow

Add a new workflow file relative to Git repository root (`D:/Project`):

- `.github/workflows/postgres-integration-tests.yml`
  (resolves to `D:/Project/.github/workflows/postgres-integration-tests.yml`;
  NOT `ad-assistant/.github/workflows/...` — GitHub Actions only triggers
  from the repository root where `.github/` resides.)

Required behavior:

- Trigger on pull requests targeting `main`.
- Trigger on pushes to this task's implementation branches:
  `ci-postgres-integration-tests` and `chore/ci-postgres-integration-tests`.
  (Narrow scope — broader push trigger matrix is a separate task.)
- Use `ubuntu-latest`.
- Use Python 3.12.
- Start PostgreSQL service container using `postgres:16`.
- Configure PostgreSQL service health check (hard requirement):
  use `pg_isready` options (e.g. `pg_isready -U postgres -d postgres`)
  so CI waits for the database to accept connections. Without this,
  race conditions between service startup and test execution can
  produce false CI failures.
- Use only temporary CI test credentials, for example:
  - database: `postgres`
  - user: `postgres`
  - password: `test`
  - port: `5432`
- Set:

```text
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres
```

- Install backend package with dev dependencies from existing project metadata.
- Run:

```bash
cd ad-assistant/cloud-backend
pytest tests/test_migrations_integration.py -v
```

Recommended install command:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Keep SQLite test behavior unchanged

This task does not need to move the existing SQLite/API suite into CI unless explicitly confirmed later. The narrow goal is PostgreSQL integration coverage.

### 3. Document CI behavior

Update:

- `docs/21-ci-postgres-integration-tests.md`
- `docs/module-context/ci-postgres-integration-tests/context.md`

The docs must explain:

- why CI owns the PG service container;
- why Codex cannot reach a developer-machine `localhost:5433`;
- how `TEST_DATABASE_URL` is set in CI;
- that no production database or real secret is used;
- how to run the same test locally.

### 4. Preserve module context

Update `docs/module-context/ci-postgres-integration-tests/context.md` with:

- implementation branch;
- changed files;
- exact workflow filename;
- test command and result;
- CI status or local workflow validation evidence;
- known risks.

If this task touches Task-02 credit-ledger docs after implementation, update `docs/module-context/sprint-02-task-02-credit-ledger/context.md` with only the new CI-related fact.

## What Not To Build

- Do not modify application code.
- Do not modify `cloud-backend/app/**`.
- Do not modify `cloud-backend/migrations/ddl/**`.
- Do not modify `cloud-backend/tests/test_migrations_integration.py` unless Codex explicitly confirms a narrow fixture/test bug.
- Do not modify `cloud-backend/tests/conftest_pg.py` unless Codex explicitly confirms a narrow fixture bug.
- Do not add or change dependencies.
- Do not add production secrets.
- Do not connect to any production, staging, or developer-shared database.
- Do not add real provider calls.
- Do not implement credit deduction, recharge, payment, orders, grants, or admin features.
- Do not modify desktop, frontend, official website, shared DTO, OpenAPI, Tauri, auth, device, usage, provider, or credit runtime behavior.
- Do not implement future provider or cost tasks.

## Allowed Files

Implementation task may modify only:

- `.github/workflows/postgres-integration-tests.yml` (new file, relative to Git repo root `D:/Project`)
- `docs/21-ci-postgres-integration-tests.md`
- `docs/module-context/ci-postgres-integration-tests/context.md`
- `docs/module-context/sprint-02-task-02-credit-ledger/context.md` (only if adding CI follow-up fact)
- `tasks/current-task.md`

## Forbidden Files

Do not modify:

- `cloud-backend/app/**`
- `cloud-backend/migrations/ddl/**`
- `cloud-backend/tests/**` unless Codex explicitly confirms a narrow fixture/test bug before implementation
- `desktop-app/**`
- `official-website/**`
- `shared/**`
- `cloud-backend/pyproject.toml`
- dependency files or lockfiles
- `.env` or `.env.example`
- provider, auth, device, usage, credit runtime services or routes

## Acceptance Criteria

- A GitHub Actions workflow exists at `.github/workflows/postgres-integration-tests.yml`
  (relative to Git repo root `D:/Project`; must NOT be placed under `ad-assistant/`).
- Workflow starts PostgreSQL `postgres:16` as a service container.
- Workflow configures PostgreSQL health check (`pg_isready`) so tests
  do not start before the database accepts connections.
- Workflow sets `TEST_DATABASE_URL` to the CI-local PostgreSQL service.
- Workflow runs `pytest tests/test_migrations_integration.py -v` from `ad-assistant/cloud-backend`.
- Workflow uses temporary CI credentials only.
- Workflow does not require repository secrets.
- Workflow does not connect to production, staging, or developer-local databases.
- No application runtime files are changed.
- No dependencies are added or upgraded.
- Documentation explains local vs CI PostgreSQL behavior.
- Module context is updated with implementation facts and test evidence.
- `git diff --check` passes.
- PR shows the PostgreSQL integration workflow running, or the implementer explains why GitHub Actions could not be observed yet.

## Test Method

Local static checks:

```bash
cd D:/Project/ad-assistant
git status --short --branch
git diff --check
```

Local optional PG verification:

```bash
cd cloud-backend
$env:TEST_DATABASE_URL='postgresql+asyncpg://postgres:test@localhost:5433/postgres'
pytest tests/test_migrations_integration.py -v
```

CI verification:

- Open PR to `main`.
- Confirm the GitHub Actions workflow starts PostgreSQL service container successfully.
- Confirm `tests/test_migrations_integration.py` passes in CI.

## Dependency Permission

No new dependencies are allowed.

The workflow may install existing project dependencies from `cloud-backend/pyproject.toml`.

## Major Change Status

Yes, this is an infrastructure/project workflow change because it adds `.github/workflows/**`.

It does not touch database schema, API contracts, provider interfaces, auth/token logic, credit/payment runtime logic, shared DTO, OpenAPI, Tauri permissions, or production deployment credentials.

User confirmation of this task sheet is required before implementation.

## Security Requirements

- Use only ephemeral PostgreSQL service container credentials inside GitHub Actions.
- Do not use repository secrets for the PostgreSQL test database.
- Do not log passwords beyond the non-secret local test value `test`.
- Do not connect to production or staging databases.
- Do not add API keys, provider keys, tokens, refresh tokens, or device fingerprints.
- Do not add remote command execution capability beyond standard CI test commands.

## Review Instructions For Codex

Review Sprint-02 Infra Task: GitHub Actions PostgreSQL Integration Tests.

Focus on:

1. Workflow scope: only PG integration CI, no business changes.
2. Service container correctness: `postgres:16`, health check, local CI URL.
3. Secret safety: no production DB, no repository secret dependency.
4. Test command: runs `tests/test_migrations_integration.py -v`.
5. File scope: only allowed files.
6. Documentation: local vs CI behavior is clear.
7. Existing local workflow remains unchanged.

Output:

- scope check;
- security check;
- CI/test reliability risks;
- whether commit is allowed.

## Completion Output Required

Implementer must report:

- changed files;
- workflow name and trigger;
- exact `TEST_DATABASE_URL` used in CI;
- test command and result;
- whether GitHub Actions actually ran;
- any residual risks;
- whether module context was updated;
- wait for Codex Review, do not self-merge.
