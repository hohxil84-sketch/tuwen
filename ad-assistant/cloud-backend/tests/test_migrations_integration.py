"""PostgreSQL DDL integration tests.

These tests validate that every ``cloud-backend/migrations/ddl/*.sql`` file
executes correctly against a real PostgreSQL database.

**All tests are automatically skipped** when ``TEST_DATABASE_URL`` is not set
(see ``tests/conftest_pg.py``).  This keeps the default ``pytest`` experience
frictionless — no local PostgreSQL required for everyday SQLite development.

Coverage
--------
* Table existence — all 6 tables created
* Column completeness — name + data-type for every column
* CHECK constraints — invalid values rejected at the database level
* FK constraints — referential integrity enforced
* Downgrade path — each DDL file contains a syntactically-valid
  ``DROP TABLE IF EXISTS`` comment
"""

import asyncio
import re
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

pytest_plugins = ["tests.conftest_pg"]

pytestmark = pytest.mark.usefixtures("pg_engine")


# ---------------------------------------------------------------------------
# Override the event_loop fixture from conftest.py — the upstream version
# calls ``asyncio.new_event_loop()`` but never calls ``set_event_loop()``,
# so asyncpg / SQLAlchemy internals that call ``get_event_loop()`` get a
# *different* loop, producing "Task got Future attached to a different loop".
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DDL_DIR = Path(__file__).resolve().parent.parent / "migrations" / "ddl"

ALL_TABLES = [
    "users",
    "devices",
    "auth_sessions",
    "risk_logs",
    "usage_events",
    "provider_call_log",
    "credit_accounts",
    "credit_ledger",
]

# Column → expected data-type substring (case-insensitive match against
# ``information_schema.columns.data_type``).  PostgreSQL reports type names
# like ``character varying`` or ``timestamp with time zone``, so we match
# on stable substrings rather than exact strings.
_EXPECTED_COLUMNS: dict[str, dict[str, str]] = {
    "users": {
        "id": "uuid",
        "account": "character varying",
        "password_hash": "character varying",
        "plan_code": "character varying",
        "status": "character varying",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
    "devices": {
        "id": "uuid",
        "user_id": "uuid",
        "device_fingerprint_hash": "character varying",
        "device_name": "character varying",
        "status": "character varying",
        "first_seen_at": "timestamp",
        "last_seen_at": "timestamp",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
    "auth_sessions": {
        "id": "uuid",
        "user_id": "uuid",
        "device_id": "uuid",
        "refresh_token_hash": "character varying",
        "expires_at": "timestamp",
        "revoked_at": "timestamp",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
    "risk_logs": {
        "id": "uuid",
        "user_id": "uuid",
        "device_id": "uuid",
        "ip_hash": "character varying",
        "event_type": "character varying",
        "severity": "character varying",
        "details": "jsonb",
        "created_at": "timestamp",
    },
    "usage_events": {
        "id": "uuid",
        "user_id": "uuid",
        "device_id": "uuid",
        "event_type": "character varying",
        "feature": "character varying",
        "request_id": "character varying",
        "metadata_json": "jsonb",
        "created_at": "timestamp",
    },
    "provider_call_log": {
        "id": "uuid",
        "request_id": "character varying",
        "user_id": "uuid",
        "device_id": "uuid",
        "provider": "character varying",
        "model": "character varying",
        "feature": "character varying",
        "status": "character varying",
        "error_code": "character varying",
        "prompt_tokens": "integer",
        "completion_tokens": "integer",
        "total_tokens": "integer",
        "estimated_cost": "numeric",
        "credits_charged": "integer",
        "latency_ms": "integer",
        "created_at": "timestamp",
    },
    "credit_accounts": {
        "id": "uuid",
        "user_id": "uuid",
        "plan_code": "character varying",
        "monthly_grant": "integer",
        "balance": "integer",
        "period_start": "timestamp",
        "period_end": "timestamp",
        "status": "character varying",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
    "credit_ledger": {
        "id": "uuid",
        "user_id": "uuid",
        "account_id": "uuid",
        "change_type": "character varying",
        "amount": "integer",
        "balance_after": "integer",
        "source_type": "character varying",
        "source_id": "character varying",
        "description": "character varying",
        "created_at": "timestamp",
    },
}

# Tables that have at least one CHECK constraint (for test-discovery).
_CHECK_TABLES: dict[str, list[dict]] = {
    "provider_call_log": [
        {
            "constraint_name": "chk_provider_call_log_status",
            "insert_sql": """\
                INSERT INTO provider_call_log
                    (id, provider, model, feature, status)
                VALUES
                    (:id, 'test', 'test', 'test', 'pending')\
            """,
            # ``status='pending'`` violates *both* chk_provider_call_log_status
            # and chk_provider_call_log_error_code; PostgreSQL may report either.
            "expect_error_contains": "chk_provider_call_log",
        },
        {
            "constraint_name": "chk_provider_call_log_prompt_tokens",
            "insert_sql": """\
                INSERT INTO provider_call_log
                    (id, provider, model, feature, status, prompt_tokens)
                VALUES
                    (:id, 'test', 'test', 'test', 'success', -1)\
            """,
            "expect_error_contains": "chk_provider_call_log_prompt_tokens",
        },
        {
            "constraint_name": "chk_provider_call_log_error_code",
            "insert_sql": """\
                INSERT INTO provider_call_log
                    (id, provider, model, feature, status, error_code)
                VALUES
                    (:id, 'test', 'test', 'test', 'success', 'SOME_ERR')\
            """,
            "expect_error_contains": "chk_provider_call_log_error_code",
        },
    ],
    "credit_accounts": [
        {
            "constraint_name": "chk_credit_accounts_balance",
            "insert_sql": """\
                INSERT INTO credit_accounts
                    (id, user_id, balance)
                VALUES
                    (:id, :uid, -1)\
            """,
            "expect_error_contains": "chk_credit_accounts_balance",
        },
        {
            "constraint_name": "chk_credit_accounts_status",
            "insert_sql": """\
                INSERT INTO credit_accounts
                    (id, user_id, status)
                VALUES
                    (:id, :uid, 'invalid_status')\
            """,
            "expect_error_contains": "chk_credit_accounts_status",
        },
        {
            "constraint_name": "chk_credit_accounts_monthly_grant",
            "insert_sql": """\
                INSERT INTO credit_accounts
                    (id, user_id, monthly_grant)
                VALUES
                    (:id, :uid, -5)\
            """,
            "expect_error_contains": "chk_credit_accounts_monthly_grant",
        },
    ],
    "credit_ledger": [
        {
            "constraint_name": "chk_credit_ledger_amount_nonzero",
            "insert_sql": """\
                INSERT INTO credit_ledger
                    (id, user_id, change_type, amount, balance_after, source_type)
                VALUES
                    (:id, :uid, 'grant', 0, 100, 'system')\
            """,
            "expect_error_contains": "chk_credit_ledger_amount_nonzero",
        },
        {
            "constraint_name": "chk_credit_ledger_balance_after",
            "insert_sql": """\
                INSERT INTO credit_ledger
                    (id, user_id, change_type, amount, balance_after, source_type)
                VALUES
                    (:id, :uid, 'consume', -50, -1, 'provider_call')\
            """,
            "expect_error_contains": "chk_credit_ledger_balance_after",
        },
        {
            "constraint_name": "chk_credit_ledger_change_type",
            "insert_sql": """\
                INSERT INTO credit_ledger
                    (id, user_id, change_type, amount, balance_after, source_type)
                VALUES
                    (:id, :uid, 'INVALID', 10, 50, 'system')\
            """,
            "expect_error_contains": "chk_credit_ledger_change_type",
        },
    ],
}

# ---------------------------------------------------------------------------
# 1. Table existence
# ---------------------------------------------------------------------------


class TestTableExistence:
    """Verify every DDL-defined table is present in PostgreSQL."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("table_name", ALL_TABLES)
    async def test_table_exists(self, pg_db, table_name: str):
        """Each table listed in ALL_TABLES must exist in ``information_schema``."""
        result = await pg_db.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table_name},
        )
        row = result.scalar_one_or_none()
        assert row == table_name, f"Table '{table_name}' not found in public schema"


# ---------------------------------------------------------------------------
# 2. Column completeness
# ---------------------------------------------------------------------------


class TestColumnCompleteness:
    """Verify every column exists and has the expected data type."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("table_name", sorted(_EXPECTED_COLUMNS.keys()))
    async def test_columns_exist(self, pg_db, table_name: str):
        """All required columns must be present."""
        expected = _EXPECTED_COLUMNS[table_name]

        result = await pg_db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table_name},
        )
        actual = {row[0] for row in result.fetchall()}
        missing = set(expected.keys()) - actual
        assert not missing, (
            f"Table '{table_name}' missing columns: {sorted(missing)}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("table_name", sorted(_EXPECTED_COLUMNS.keys()))
    async def test_column_types(self, pg_db, table_name: str):
        """Each column's data type must contain the expected substring."""
        expected = _EXPECTED_COLUMNS[table_name]

        result = await pg_db.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table_name},
        )
        actual_types: dict[str, str] = {
            row[0]: row[1].lower() for row in result.fetchall()
        }

        mismatches: list[str] = []
        for col_name, type_substr in expected.items():
            actual = actual_types.get(col_name, "")
            if type_substr not in actual:
                mismatches.append(
                    f"  {col_name}: expected type containing '{type_substr}', "
                    f"got '{actual}'"
                )
        assert not mismatches, (
            f"Table '{table_name}' type mismatches:\n" + "\n".join(mismatches)
        )


# ---------------------------------------------------------------------------
# 3. CHECK constraints
# ---------------------------------------------------------------------------


class TestCheckConstraintNames:
    """Verify that named CHECK constraints are registered in pg_constraint."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "table_name,constraint_name",
        [
            (t, c["constraint_name"])
            for t, cases in _CHECK_TABLES.items()
            for c in cases
        ],
    )
    async def test_check_constraint_exists(
        self, pg_db, table_name: str, constraint_name: str
    ):
        """The named CHECK constraint must be registered."""
        result = await pg_db.execute(
            text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conname = :cname "
                "AND conrelid = (SELECT oid FROM pg_class WHERE relname = :tbl)"
            ),
            {"cname": constraint_name, "tbl": table_name},
        )
        assert result.scalar_one_or_none() is not None, (
            f"Constraint '{constraint_name}' not found on table '{table_name}'"
        )


class TestCheckConstraintEnforcement:
    """Verify that CHECK constraints actually reject invalid data."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(c, id=c["constraint_name"])
            for cases in _CHECK_TABLES.values()
            for c in cases
        ],
    )
    async def test_check_constraint_rejects_invalid(
        self, pg_db, case: dict
    ):
        """Invalid INSERT must raise IntegrityError referencing the CHECK name."""
        sql = case["insert_sql"]
        expected_fragment = case["expect_error_contains"]

        # 需要 user FK 的表，先创建一个测试用户
        params: dict = {"id": uuid.uuid4()}
        if ":uid" in sql:
            seed_uid = uuid.uuid4()
            await pg_db.execute(
                text(
                    "INSERT INTO users (id, account, password_hash) "
                    "VALUES (:id, :account, :pw)"
                ),
                {
                    "id": seed_uid,
                    "account": f"check_test_{seed_uid.hex[:8]}@test.com",
                    "pw": "hashed",
                },
            )
            params["uid"] = seed_uid

        with pytest.raises(IntegrityError) as exc_info:
            await pg_db.execute(text(sql), params)

        # The error should mention the constraint name — but asyncpg wraps it
        # inside the exception message.  We check both the str() and any
        # available __cause__.
        error_text = str(exc_info.value).lower()
        if exc_info.value.__cause__ is not None:
            error_text += " " + str(exc_info.value.__cause__).lower()

        assert expected_fragment.lower() in error_text, (
            f"Expected error to reference '{expected_fragment}', "
            f"but got: {str(exc_info.value)[:300]}"
        )


# ---------------------------------------------------------------------------
# 4. FK constraints
# ---------------------------------------------------------------------------


class TestForeignKeyConstraints:
    """Verify referential integrity between tables."""

    @pytest.mark.asyncio
    async def test_devices_rejects_invalid_user_id(self, pg_db):
        """Inserting a device with a non-existent user_id must fail."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(IntegrityError) as exc_info:
            await pg_db.execute(
                text(
                    "INSERT INTO devices (id, user_id, device_fingerprint_hash) "
                    "VALUES (:id, :uid, :fp)"
                ),
                {
                    "id": uuid.uuid4(),
                    "uid": fake_user_id,
                    "fp": "test-fingerprint-hash",
                },
            )

        error_text = str(exc_info.value).lower()
        if exc_info.value.__cause__ is not None:
            error_text += " " + str(exc_info.value.__cause__).lower()
        assert "foreign key" in error_text or "devices_user_id_fkey" in error_text or (
            "violates" in error_text and "foreign" in error_text
        ), (
            f"Expected FK violation, got: {str(exc_info.value)[:300]}"
        )

    @pytest.mark.asyncio
    async def test_auth_sessions_rejects_invalid_refs(self, pg_db):
        """auth_sessions FK to users/devices must be enforced."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(IntegrityError) as exc_info:
            await pg_db.execute(
                text(
                    "INSERT INTO auth_sessions "
                    "(id, user_id, device_id, refresh_token_hash, expires_at) "
                    "VALUES (:id, :uid, :did, :hash, NOW() + INTERVAL '1 day')"
                ),
                {
                    "id": uuid.uuid4(),
                    "uid": fake_id,
                    "did": fake_id,
                    "hash": "test-token-hash",
                },
            )

        error_text = str(exc_info.value).lower()
        if exc_info.value.__cause__ is not None:
            error_text += " " + str(exc_info.value.__cause__).lower()
        assert "foreign" in error_text, (
            f"Expected FK violation, got: {str(exc_info.value)[:300]}"
        )

    @pytest.mark.asyncio
    async def test_credit_accounts_rejects_invalid_user_id(self, pg_db):
        """credit_accounts FK to users must be enforced."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(IntegrityError) as exc_info:
            await pg_db.execute(
                text(
                    "INSERT INTO credit_accounts (id, user_id) "
                    "VALUES (:id, :uid)"
                ),
                {"id": uuid.uuid4(), "uid": fake_user_id},
            )

        error_text = str(exc_info.value).lower()
        if exc_info.value.__cause__ is not None:
            error_text += " " + str(exc_info.value.__cause__).lower()
        assert "foreign" in error_text, (
            f"Expected FK violation, got: {str(exc_info.value)[:300]}"
        )

    @pytest.mark.asyncio
    async def test_credit_ledger_rejects_invalid_user_id(self, pg_db):
        """credit_ledger FK to users must be enforced."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(IntegrityError) as exc_info:
            await pg_db.execute(
                text(
                    "INSERT INTO credit_ledger "
                    "(id, user_id, change_type, amount, balance_after, source_type) "
                    "VALUES (:id, :uid, 'grant', 100, 100, 'system')"
                ),
                {"id": uuid.uuid4(), "uid": fake_user_id},
            )

        error_text = str(exc_info.value).lower()
        if exc_info.value.__cause__ is not None:
            error_text += " " + str(exc_info.value.__cause__).lower()
        assert "foreign" in error_text, (
            f"Expected FK violation, got: {str(exc_info.value)[:300]}"
        )


# ---------------------------------------------------------------------------
# 5. Downgrade path
# ---------------------------------------------------------------------------

_DOWNGRADE_RE = re.compile(
    r"^--\s*(DROP TABLE IF EXISTS\s+.+;)\s*$", re.MULTILINE
)


class TestDowngradePath:
    """Verify each DDL file carries a syntactically-valid downgrade comment."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ddl_filename", sorted(p.name for p in DDL_DIR.glob("*.sql")))
    async def test_ddl_has_drop_comment(self, ddl_filename: str):
        """Every DDL file must contain a ``-- DROP TABLE IF EXISTS`` comment."""
        path = DDL_DIR / ddl_filename
        content = path.read_text(encoding="utf-8")
        m = _DOWNGRADE_RE.search(content)
        assert m is not None, (
            f"DDL file '{ddl_filename}' is missing a "
            f"'-- DROP TABLE IF EXISTS <table>' comment"
        )

    @pytest.mark.asyncio
    async def test_drop_statements_are_valid_sql(self, pg_db):
        """All extracted DROP statements execute without error."""
        ddl_files = sorted(DDL_DIR.glob("*.sql"))

        drops: list[str] = []
        for ddl_path in ddl_files:
            content = ddl_path.read_text(encoding="utf-8")
            m = _DOWNGRADE_RE.search(content)
            if m:
                drops.append(m.group(1))

        # Verify against current PG: drop in reverse order
        for drop_sql in reversed(drops):
            await pg_db.execute(text(drop_sql))
