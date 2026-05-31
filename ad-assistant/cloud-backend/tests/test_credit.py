"""Credit API and service tests — table structure, auth, balance, ledger, service validation."""

import uuid

import pytest

from app.core.security import create_access_token
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.user import User
from app.services.credit_service import (
    get_credit_balance,
    get_or_create_credit_account,
    list_credit_ledger,
    record_credit_ledger,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_header(test_user, test_device):
    """构建测试用 Authorization header."""
    token = create_access_token(
        sub=str(test_user.id),
        device_id=str(test_device.id),
        plan=test_user.plan_code,
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. 表结构测试
# ---------------------------------------------------------------------------


class TestCreditAccountTable:
    """credit_accounts 表结构和列验证."""

    async def test_table_exists(self, db_session):
        """credit_accounts 表应存在且可通过 ORM 查询."""
        result = await db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='credit_accounts'"
            )
        )
        row = result.scalar_one_or_none()
        assert row == "credit_accounts"

    async def test_columns_match_schema(self, db_session):
        """确认表包含所有必需列."""
        result = await db_session.execute(
            __import__("sqlalchemy").text("PRAGMA table_info('credit_accounts')")
        )
        columns = {row[1] for row in result.fetchall()}
        required = {
            "id", "user_id", "plan_code", "monthly_grant", "balance",
            "period_start", "period_end", "status", "created_at", "updated_at",
        }
        assert required.issubset(columns)


class TestCreditLedgerTable:
    """credit_ledger 表结构和列验证."""

    async def test_table_exists(self, db_session):
        """credit_ledger 表应存在且可通过 ORM 查询."""
        result = await db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='credit_ledger'"
            )
        )
        row = result.scalar_one_or_none()
        assert row == "credit_ledger"

    async def test_columns_match_schema(self, db_session):
        """确认表包含所有必需列."""
        result = await db_session.execute(
            __import__("sqlalchemy").text("PRAGMA table_info('credit_ledger')")
        )
        columns = {row[1] for row in result.fetchall()}
        required = {
            "id", "user_id", "account_id", "change_type", "amount",
            "balance_after", "source_type", "source_id", "description", "created_at",
        }
        assert required.issubset(columns)


# ---------------------------------------------------------------------------
# 2. 鉴权测试
# ---------------------------------------------------------------------------


class TestCreditAuth:
    """Credit API 鉴权测试."""

    async def test_balance_no_auth_returns_401(self, client):
        """无 token 访问 balance → 401."""
        res = await client.get("/api/v1/credits/balance")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_ledger_no_auth_returns_401(self, client):
        """无 token 访问 ledger → 401."""
        res = await client.get("/api/v1/credits/ledger")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"


# ---------------------------------------------------------------------------
# 3. 用户隔离测试
# ---------------------------------------------------------------------------


class TestCreditUserIsolation:
    """用户只能看到自己的 balance 和 ledger."""

    async def test_user_cannot_see_other_balance(
        self, client, db_session, test_user, test_device
    ):
        """用户 A 查询 balance 只能看到自己的账户."""
        # 创建用户 B
        user_b = User(
            id=uuid.uuid4(),
            account="other@example.com",
            password_hash="hashed",
            plan_code="standard",
            status="active",
        )
        db_session.add(user_b)
        await db_session.flush()

        # 为用户 B 创建账户，余额 100
        account_b = CreditAccount(
            user_id=user_b.id,
            plan_code="standard",
            balance=100,
            status="active",
        )
        db_session.add(account_b)
        await db_session.flush()

        # test_user 查询自己的 balance
        res = await client.get(
            "/api/v1/credits/balance",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["user_id"] == str(test_user.id)
        # test_user 的余额应当为 0（首次创建），不应看到 user_b 的 100
        assert body["data"]["balance"] == 0

    async def test_user_cannot_see_other_ledger(
        self, client, db_session, test_user, test_device
    ):
        """用户 A 查询 ledger 只能看到自己的流水."""
        # 创建用户 B
        user_b = User(
            id=uuid.uuid4(),
            account="ledger_other@example.com",
            password_hash="hashed",
            plan_code="standard",
            status="active",
        )
        db_session.add(user_b)
        await db_session.flush()

        # 为用户 B 写入一条流水
        ledger_b = CreditLedger(
            user_id=user_b.id,
            change_type="grant",
            amount=500,
            balance_after=500,
            source_type="system",
        )
        db_session.add(ledger_b)
        await db_session.flush()

        # test_user 查询自己的 ledger
        res = await client.get(
            "/api/v1/credits/ledger",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        for item in body["data"]["items"]:
            assert item["user_id"] == str(test_user.id)


# ---------------------------------------------------------------------------
# 4. Balance 查询测试
# ---------------------------------------------------------------------------


class TestCreditBalance:
    """Balance API 功能测试."""

    async def test_first_query_creates_account_with_zero_balance(
        self, client, db_session, test_user, test_device
    ):
        """首次查询 balance 会创建基础账户，余额为 0."""
        # 确认此用户还没有账户
        result = await db_session.execute(
            __import__("sqlalchemy").select(CreditAccount).where(
                CreditAccount.user_id == test_user.id
            )
        )
        assert result.scalar_one_or_none() is None

        # 查询 balance
        res = await client.get(
            "/api/v1/credits/balance",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["user_id"] == str(test_user.id)
        assert body["data"]["balance"] == 0
        assert body["data"]["plan_code"] == "standard"
        assert body["data"]["status"] == "active"
        assert body["data"]["monthly_grant"] == 0

        # 确认账户已持久化
        account = (
            await db_session.execute(
                __import__("sqlalchemy").select(CreditAccount).where(
                    CreditAccount.user_id == test_user.id
                )
            )
        ).scalar_one_or_none()
        assert account is not None
        assert account.balance == 0

    async def test_balance_returns_existing_balance(
        self, client, db_session, test_user, test_device
    ):
        """已有账户时直接返回现有余额."""
        account = CreditAccount(
            user_id=test_user.id,
            plan_code="expert",
            balance=300,
            status="active",
        )
        db_session.add(account)
        await db_session.flush()

        res = await client.get(
            "/api/v1/credits/balance",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["balance"] == 300
        assert body["data"]["plan_code"] == "expert"


# ---------------------------------------------------------------------------
# 5. Ledger 查询测试
# ---------------------------------------------------------------------------


class TestCreditLedger:
    """Ledger API 功能测试."""

    async def test_empty_ledger_for_new_user(self, client, test_user, test_device):
        """新用户流水为空."""
        res = await client.get(
            "/api/v1/credits/ledger",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

    async def test_ledger_pagination(self, client, db_session, test_user, test_device):
        """流水支持分页，按时间倒序."""
        import time as _time

        # 写入 5 条流水
        for i in range(5):
            ledger = CreditLedger(
                user_id=test_user.id,
                change_type="grant",
                amount=100 * (i + 1),
                balance_after=100 * (i + 1),
                source_type="system",
            )
            db_session.add(ledger)
        await db_session.flush()

        # limit=2
        res = await client.get(
            "/api/v1/credits/ledger?limit=2&offset=0",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["limit"] == 2
        assert body["data"]["offset"] == 0
        assert len(body["data"]["items"]) == 2
        assert body["data"]["total"] >= 5

    async def test_ledger_desc_order(self, client, db_session, test_user, test_device):
        """流水按 created_at 倒序返回."""
        from datetime import datetime, timedelta, timezone

        base = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)

        # 写入 3 条流水，用显式递增时间戳确保可验证倒序
        for i in range(3):
            ledger = CreditLedger(
                user_id=test_user.id,
                change_type="grant",
                amount=100 * (i + 1),
                balance_after=100 * (i + 1),
                source_type="system",
                created_at=base + timedelta(seconds=i * 10),
            )
            db_session.add(ledger)
        await db_session.flush()

        res = await client.get(
            "/api/v1/credits/ledger",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        items = body["data"]["items"]
        assert len(items) >= 3

        # 提取 created_at 并断言严格倒序（最新的在前）
        timestamps = [item["created_at"] for item in items if item["created_at"]]
        assert len(timestamps) >= 3, f"Expected at least 3 timestamps, got {len(timestamps)}"
        assert timestamps == sorted(timestamps, reverse=True), (
            f"Ledger items should be sorted by created_at DESC, "
            f"got {timestamps}"
        )


# ---------------------------------------------------------------------------
# 6. Service 校验测试
# ---------------------------------------------------------------------------


class TestCreditServiceValidation:
    """record_credit_ledger 参数校验."""

    async def test_rejects_invalid_change_type(self, db_session, test_user):
        """非法 change_type 抛出 ValueError."""
        with pytest.raises(ValueError, match="Invalid change_type"):
            await record_credit_ledger(
                db=db_session,
                user_id=test_user.id,
                account_id=None,
                change_type="INVALID",
                amount=100,
                balance_after=100,
                source_type="system",
            )

    async def test_rejects_invalid_source_type(self, db_session, test_user):
        """非法 source_type 抛出 ValueError."""
        with pytest.raises(ValueError, match="Invalid source_type"):
            await record_credit_ledger(
                db=db_session,
                user_id=test_user.id,
                account_id=None,
                change_type="grant",
                amount=100,
                balance_after=100,
                source_type="INVALID",
            )

    async def test_rejects_zero_amount(self, db_session, test_user):
        """amount=0 抛出 ValueError."""
        with pytest.raises(ValueError, match="amount must not be 0"):
            await record_credit_ledger(
                db=db_session,
                user_id=test_user.id,
                account_id=None,
                change_type="grant",
                amount=0,
                balance_after=100,
                source_type="system",
            )

    async def test_rejects_negative_balance_after(self, db_session, test_user):
        """balance_after < 0 抛出 ValueError."""
        with pytest.raises(ValueError, match="balance_after must be >= 0"):
            await record_credit_ledger(
                db=db_session,
                user_id=test_user.id,
                account_id=None,
                change_type="consume",
                amount=-100,
                balance_after=-1,
                source_type="provider_call",
            )

    async def test_consume_must_be_negative(self, db_session, test_user):
        """consume 类型 amount 必须为负."""
        with pytest.raises(ValueError, match="consume amount must be negative"):
            await record_credit_ledger(
                db=db_session,
                user_id=test_user.id,
                account_id=None,
                change_type="consume",
                amount=100,
                balance_after=200,
                source_type="provider_call",
            )

    async def test_record_credit_ledger_success(self, db_session, test_user):
        """正常写入流水成功."""
        account = CreditAccount(
            user_id=test_user.id,
            balance=500,
            status="active",
        )
        db_session.add(account)
        await db_session.flush()

        ledger = await record_credit_ledger(
            db=db_session,
            user_id=test_user.id,
            account_id=account.id,
            change_type="consume",
            amount=-50,
            balance_after=450,
            source_type="provider_call",
            source_id="call_001",
            description="Test consume",
        )
        assert ledger.id is not None
        assert ledger.change_type == "consume"
        assert ledger.amount == -50
        assert ledger.balance_after == 450

        # 确认已持久化
        stmt = (
            __import__("sqlalchemy")
            .select(CreditLedger)
            .where(CreditLedger.id == ledger.id)
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.change_type == "consume"


# ---------------------------------------------------------------------------
# 7. Service 账户测试
# ---------------------------------------------------------------------------


class TestCreditAccountService:
    """get_or_create_credit_account 和 get_credit_balance 测试."""

    async def test_get_or_create_new(self, db_session, test_user):
        """用户无账户时创建并返回."""
        account = await get_or_create_credit_account(db=db_session, user_id=test_user.id)
        assert account is not None
        assert account.user_id == test_user.id
        assert account.balance == 0
        assert account.status == "active"
        assert account.plan_code == "standard"

    async def test_get_or_create_existing(self, db_session, test_user):
        """已有账户时直接返回."""
        existing = CreditAccount(
            user_id=test_user.id,
            plan_code="expert",
            balance=999,
            status="active",
        )
        db_session.add(existing)
        await db_session.flush()

        account = await get_or_create_credit_account(db=db_session, user_id=test_user.id)
        assert account.id == existing.id
        assert account.balance == 999
        assert account.plan_code == "expert"

    async def test_get_credit_balance_new_user(self, db_session, test_user):
        """新用户 get_credit_balance 返回余额 0."""
        data = await get_credit_balance(db=db_session, user_id=test_user.id)
        assert data["user_id"] == str(test_user.id)
        assert data["balance"] == 0
        assert data["status"] == "active"
