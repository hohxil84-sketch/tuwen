"""PostgreSQL integration test fixtures.

Usage::

    TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \\
        pytest tests/test_migrations_integration.py -v

If ``TEST_DATABASE_URL`` is not set, every test that depends on the
``pg_engine`` fixture is automatically skipped so that the absence of a
local PostgreSQL instance never blocks the main SQLite test suite.
"""

import os
import re
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DDL_DIR = Path(__file__).resolve().parent.parent / "migrations" / "ddl"

_DOWNGRADE_RE = re.compile(
    r"^--\s*(DROP TABLE IF EXISTS\s+.+;)\s*$", re.MULTILINE
)

def _strip_downgrade(sql: str) -> str:
    """Remove downgrade-related comment lines so they are not executed."""
    lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- Downgrade:") or stripped.startswith(
            "-- DROP TABLE"
        ):
            continue
        lines.append(line)
    return "\n".join(lines)


def _split_statements(sql: str) -> list[str]:
    """Split multi-statement SQL into individual statements.

    Empty / whitespace-only entries are dropped.
    """
    return [s.strip() for s in sql.split(";") if s.strip()]


def _extract_drop(ddl_text: str) -> str | None:
    """Extract the ``DROP TABLE IF EXISTS ...`` line from a DDL file."""
    m = _DOWNGRADE_RE.search(ddl_text)
    if m is None:
        return None
    return m.group(1)


# ---------------------------------------------------------------------------
# Session-scoped engine
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def pg_engine():
    """Async SQLAlchemy engine connected to a real PostgreSQL instance.

    * Reads ``TEST_DATABASE_URL`` from the environment.
    * Skips the **entire session** when the variable is absent.
    * Executes DDL files ``001`` → ``008`` in order on setup.
    * Executes ``DROP TABLE IF EXISTS`` in reverse order on teardown.
    """
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL not set")

    engine = create_async_engine(database_url, echo=False, poolclass=NullPool)

    # ---- Setup: apply all DDL in order -------------------------------------
    ddl_files = sorted(DDL_DIR.glob("*.sql"))
    assert len(ddl_files) == 10, f"Expected 10 DDL files, found {len(ddl_files)}"

    async with engine.begin() as conn:
        for ddl_path in ddl_files:
            ddl_text = ddl_path.read_text(encoding="utf-8")
            sql = _strip_downgrade(ddl_text)
            for stmt in _split_statements(sql):
                await conn.execute(text(stmt))

    yield engine

    # ---- Teardown: drop tables in reverse creation order -------------------
    drops: list[str] = []
    for ddl_path in reversed(ddl_files):
        ddl_text = ddl_path.read_text(encoding="utf-8")
        drop = _extract_drop(ddl_text)
        if drop:
            drops.append(drop)

    async with engine.begin() as conn:
        for drop in drops:
            await conn.execute(text(drop))

    await engine.dispose()


# ---------------------------------------------------------------------------
# Per-test connection fixture — each test runs inside a transaction that is
# rolled back after the test, mirroring the ``db_session`` pattern.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def pg_db(pg_engine):
    """Yield a connection wrapped in a transaction, rolled back after each test.

    Mirrors the ``db_session`` fixture from ``conftest.py`` so that every
    integration test starts in a fresh transaction and never leaves side
    effects behind — even DROP TABLE tests are rolled back.
    """
    async with pg_engine.connect() as conn:
        async with conn.begin() as trans:
            yield conn
            await trans.rollback()
