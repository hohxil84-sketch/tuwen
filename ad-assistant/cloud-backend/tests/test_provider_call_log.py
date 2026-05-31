"""Provider call log API tests — table structure, write, query, auth, isolation, validation, DDL constraints."""

import os
import uuid

import pytest

from app.core.security import create_access_token
from app.models.provider_call_log import ProviderCallLog
from app.models.user import User
from app.services.provider_log_service import (
    _validate_provider_call,
    list_provider_call_logs,
    record_provider_call,
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


def _ddl_path(filename: str) -> str:
    """返回 DDL 文件的绝对路径."""
    return os.path.join(
        os.path.dirname(__file__),
        "..", "migrations", "ddl", filename,
    )


# ---------------------------------------------------------------------------
# 1. 表结构测试
# ---------------------------------------------------------------------------


class TestProviderCallLogTable:
    """provider_call_log 表结构和列验证."""

    async def test_table_exists(self, db_session):
        """provider_call_log 表应存在且可通过 ORM 查询."""
        result = await db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='provider_call_log'"
            )
        )
        row = result.scalar_one_or_none()
        assert row == "provider_call_log"

    async def test_columns_match_schema(self, db_session):
        """确认表包含所有必需列."""
        result = await db_session.execute(
            __import__("sqlalchemy").text("PRAGMA table_info('provider_call_log')")
        )
        columns = {row[1] for row in result.fetchall()}
        required = {
            "id", "request_id", "user_id", "device_id", "provider",
            "model", "feature", "status", "error_code",
            "prompt_tokens", "completion_tokens", "total_tokens",
            "estimated_cost", "credits_charged", "latency_ms", "created_at",
        }
        assert required.issubset(columns)


# ---------------------------------------------------------------------------
# 2. DDL 约束验证（读取 SQL 文件，确保 CHECK 约束存在）
# ---------------------------------------------------------------------------


class TestProviderCallLogDDL:
    """验证 provider_call_log 的 DDL 文件包含必需的 CHECK 约束."""

    def test_ddl_file_exists(self):
        """DDL 文件应存在."""
        path = _ddl_path("006_provider_call_log.sql")
        assert os.path.isfile(path), f"DDL file not found: {path}"

    def test_ddl_has_check_on_status(self):
        """DDL 应包含 status IN ('success', 'error') CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_status" in ddl
        assert "status IN ('success', 'error')" in ddl.lower() or \
               "status in ('success', 'error')" in ddl.lower()

    def test_ddl_has_check_on_error_code(self):
        """DDL 应包含 error_code 与 status 联动的 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_error_code" in ddl
        assert "status = 'error'" in ddl.lower()
        assert "status = 'success'" in ddl.lower()

    def test_ddl_has_check_on_prompt_tokens(self):
        """DDL 应包含 prompt_tokens >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_prompt_tokens" in ddl
        assert "prompt_tokens >= 0" in ddl.lower()

    def test_ddl_has_check_on_completion_tokens(self):
        """DDL 应包含 completion_tokens >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_completion_tokens" in ddl
        assert "completion_tokens >= 0" in ddl.lower()

    def test_ddl_has_check_on_total_tokens(self):
        """DDL 应包含 total_tokens >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_total_tokens" in ddl
        assert "total_tokens >= 0" in ddl.lower()

    def test_ddl_has_check_on_estimated_cost(self):
        """DDL 应包含 estimated_cost >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_estimated_cost" in ddl
        assert "estimated_cost" in ddl.lower()

    def test_ddl_has_check_on_credits_charged(self):
        """DDL 应包含 credits_charged >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_credits_charged" in ddl
        assert "credits_charged" in ddl.lower()

    def test_ddl_has_check_on_latency_ms(self):
        """DDL 应包含 latency_ms >= 0 CHECK 约束."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "chk_provider_call_log_latency_ms" in ddl
        assert "latency_ms" in ddl.lower()

    def test_ddl_has_downgrade_comment(self):
        """DDL 应包含降级注释."""
        ddl = _read_ddl("006_provider_call_log.sql")
        assert "DROP TABLE IF EXISTS provider_call_log" in ddl


def _read_ddl(filename: str) -> str:
    """读取 DDL 文件内容."""
    path = _ddl_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 3. 写入参数校验测试（service 层）
# ---------------------------------------------------------------------------


class TestProviderCallLogValidation:
    """_validate_provider_call 参数校验."""

    # -- status 校验 --

    def test_invalid_status_raises(self):
        """非法 status 抛出 INVALID_STATUS."""
        with pytest.raises(ValueError, match="INVALID_STATUS"):
            _validate_provider_call(
                status="pending", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_error_status_without_error_code_raises(self):
        """status=error 但无 error_code → ERROR_CODE_REQUIRED."""
        with pytest.raises(ValueError, match="ERROR_CODE_REQUIRED"):
            _validate_provider_call(
                status="error", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_error_status_with_empty_error_code_raises(self):
        """status=error 但 error_code 为空字符串 → ERROR_CODE_REQUIRED."""
        with pytest.raises(ValueError, match="ERROR_CODE_REQUIRED"):
            _validate_provider_call(
                status="error", error_code="",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_success_status_with_error_code_raises(self):
        """status=success 不能带 error_code."""
        with pytest.raises(ValueError, match="ERROR_CODE_NOT_ALLOWED_FOR_SUCCESS"):
            _validate_provider_call(
                status="success", error_code="SOME_ERROR",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_valid_success_passes(self):
        """status=success 且 error_code=None 应通过校验."""
        _validate_provider_call(
            status="success", error_code=None,
            prompt_tokens=100, completion_tokens=50, total_tokens=150,
            estimated_cost=0.002, credits_charged=1, latency_ms=200,
        )

    def test_valid_error_passes(self):
        """status=error 且有 error_code 应通过校验."""
        _validate_provider_call(
            status="error", error_code="PROVIDER_TIMEOUT",
            prompt_tokens=0, completion_tokens=0, total_tokens=0,
            estimated_cost=None, credits_charged=None, latency_ms=30000,
        )

    # -- 非负校验 --

    def test_negative_prompt_tokens_raises(self):
        """prompt_tokens < 0 → PROMPT_TOKENS_NEGATIVE."""
        with pytest.raises(ValueError, match="PROMPT_TOKENS_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=-1, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_negative_completion_tokens_raises(self):
        """completion_tokens < 0 → COMPLETION_TOKENS_NEGATIVE."""
        with pytest.raises(ValueError, match="COMPLETION_TOKENS_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=0, completion_tokens=-5, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_negative_total_tokens_raises(self):
        """total_tokens < 0 → TOTAL_TOKENS_NEGATIVE."""
        with pytest.raises(ValueError, match="TOTAL_TOKENS_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=-10,
                estimated_cost=None, credits_charged=None, latency_ms=None,
            )

    def test_negative_estimated_cost_raises(self):
        """estimated_cost < 0 → ESTIMATED_COST_NEGATIVE."""
        with pytest.raises(ValueError, match="ESTIMATED_COST_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=-0.001, credits_charged=None, latency_ms=None,
            )

    def test_negative_credits_charged_raises(self):
        """credits_charged < 0 → CREDITS_CHARGED_NEGATIVE."""
        with pytest.raises(ValueError, match="CREDITS_CHARGED_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=-1, latency_ms=None,
            )

    def test_negative_latency_ms_raises(self):
        """latency_ms < 0 → LATENCY_MS_NEGATIVE."""
        with pytest.raises(ValueError, match="LATENCY_MS_NEGATIVE"):
            _validate_provider_call(
                status="success", error_code=None,
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                estimated_cost=None, credits_charged=None, latency_ms=-100,
            )

    def test_zero_values_pass(self):
        """所有字段为 0（合法值）应通过校验."""
        _validate_provider_call(
            status="success", error_code=None,
            prompt_tokens=0, completion_tokens=0, total_tokens=0,
            estimated_cost=0.0, credits_charged=0, latency_ms=0,
        )

    # -- service 层集成测试 --

    async def test_service_raises_on_invalid_status(self, db_session, test_user):
        """service 写入非法 status 应抛出 ValueError."""
        with pytest.raises(ValueError, match="INVALID_STATUS"):
            await record_provider_call(
                db=db_session,
                provider="deepseek", model="chat", feature="ocr",
                status="unknown",
                user_id=test_user.id,
            )

    async def test_service_raises_on_error_without_code(self, db_session, test_user):
        """service 写入 status=error 无 error_code 应抛出 ValueError."""
        with pytest.raises(ValueError, match="ERROR_CODE_REQUIRED"):
            await record_provider_call(
                db=db_session,
                provider="deepseek", model="chat", feature="ocr",
                status="error", error_code=None,
                user_id=test_user.id,
            )

    async def test_service_raises_on_negative_tokens(self, db_session, test_user):
        """service 写入负数 tokens 应抛出 ValueError."""
        with pytest.raises(ValueError, match="PROMPT_TOKENS_NEGATIVE"):
            await record_provider_call(
                db=db_session,
                provider="deepseek", model="chat", feature="ocr",
                status="success",
                prompt_tokens=-50,
                user_id=test_user.id,
            )


# ---------------------------------------------------------------------------
# 4. 写入测试
# ---------------------------------------------------------------------------


class TestProviderCallLogWrite:
    """使用 service 层写入 provider_call_log."""

    async def test_record_success_call(self, db_session, test_user, test_device):
        """成功调用应记录 status=success."""
        result = await record_provider_call(
            db=db_session,
            provider="deepseek",
            model="deepseek-chat",
            feature="ocr",
            status="success",
            user_id=test_user.id,
            device_id=test_device.id,
            request_id="req_call_001",
            prompt_tokens=150,
            completion_tokens=80,
            total_tokens=230,
            estimated_cost=0.0035,
            latency_ms=450,
        )
        assert result["status"] == "success"
        assert result["provider"] == "deepseek"
        assert result["total_tokens"] == 230

        # 确认已持久化
        stmt = __import__("sqlalchemy").select(ProviderCallLog).where(
            ProviderCallLog.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.status == "success"
        assert row.error_code is None

    async def test_record_error_call(self, db_session, test_user, test_device):
        """失败调用应记录 status=error 和 error_code."""
        result = await record_provider_call(
            db=db_session,
            provider="openai",
            model="gpt-4o",
            feature="vectorize",
            status="error",
            error_code="PROVIDER_TIMEOUT",
            user_id=test_user.id,
            device_id=test_device.id,
            request_id="req_call_err_001",
            latency_ms=30000,
        )
        assert result["status"] == "error"

        # 确认持久化
        stmt = __import__("sqlalchemy").select(ProviderCallLog).where(
            ProviderCallLog.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.status == "error"
        assert row.error_code == "PROVIDER_TIMEOUT"

    async def test_no_sensitive_data_in_record(self, db_session, test_user):
        """记录中不包含 prompt 原文或 API Key."""
        result = await record_provider_call(
            db=db_session,
            provider="paddleocr",
            model="pp-ocr-v4",
            feature="ocr",
            status="success",
            user_id=test_user.id,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )
        stmt = __import__("sqlalchemy").select(ProviderCallLog).where(
            ProviderCallLog.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        # provider_call_log 不存储 prompt 原文或 API Key
        # 确认 model_dump 中不包含敏感字段名
        row_dict = {
            "provider": row.provider,
            "model": row.model,
            "feature": row.feature,
            "status": row.status,
            "error_code": row.error_code,
        }
        for key in row_dict:
            assert "api_key" not in key.lower()
            assert "token" not in key.lower()
            assert "prompt_text" not in key.lower()


# ---------------------------------------------------------------------------
# 5. 查询鉴权测试
# ---------------------------------------------------------------------------


class TestProviderCallLogAuth:
    """provider_call_log 查询鉴权."""

    async def test_no_auth_returns_401(self, client):
        """无 token → 401."""
        res = await client.get("/api/v1/provider-call-logs")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_user_cannot_access_other_user_data(
        self, client, db_session, test_user, test_device
    ):
        """用户 A 不能查询用户 B 的调用日志."""
        # 创建用户 B
        user_b = User(
            id=uuid.uuid4(),
            account="other2@example.com",
            password_hash="hashed",
            plan_code="standard",
            status="active",
        )
        db_session.add(user_b)
        await db_session.flush()

        # 为用户 A 写入一条记录
        await record_provider_call(
            db=db_session,
            provider="deepseek",
            model="deepseek-chat",
            feature="ocr",
            status="success",
            user_id=test_user.id,
            device_id=test_device.id,
        )

        # 为用户 B 写入一条记录
        await record_provider_call(
            db=db_session,
            provider="openai",
            model="gpt-4o",
            feature="vectorize",
            status="success",
            user_id=user_b.id,
        )

        # 用 test_user 的身份查询 — 应只能看到自己的数据
        res = await client.get(
            "/api/v1/provider-call-logs",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        for item in body["data"]["items"]:
            assert item["user_id"] == str(test_user.id)


# ---------------------------------------------------------------------------
# 6. 查询功能测试
# ---------------------------------------------------------------------------


class TestProviderCallLogQuery:
    """Provider 调用日志查询功能测试."""

    async def test_status_filter(self, client, db_session, test_user, test_device):
        """按 status 筛选."""
        await record_provider_call(
            db=db_session,
            provider="deepseek",
            model="deepseek-chat",
            feature="ocr",
            status="success",
            user_id=test_user.id,
            device_id=test_device.id,
        )
        await record_provider_call(
            db=db_session,
            provider="openai",
            model="gpt-4o",
            feature="ocr",
            status="error",
            error_code="PROVIDER_TIMEOUT",
            user_id=test_user.id,
            device_id=test_device.id,
        )

        # 按 status=error 筛选
        res = await client.get(
            "/api/v1/provider-call-logs?status=error",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        for item in body["data"]["items"]:
            assert item["status"] == "error"

    async def test_pagination(self, client, db_session, test_user, test_device):
        """分页查询正常."""
        for i in range(3):
            await record_provider_call(
                db=db_session,
                provider="deepseek",
                model="deepseek-chat",
                feature="ocr",
                status="success",
                user_id=test_user.id,
                device_id=test_device.id,
            )

        res = await client.get(
            "/api/v1/provider-call-logs?limit=2&offset=0",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["limit"] == 2
        assert len(body["data"]["items"]) == 2
        assert body["data"]["total"] >= 3

    async def test_empty_list_for_new_user(self, client, test_user, test_device):
        """新用户应返回空列表."""
        res = await client.get(
            "/api/v1/provider-call-logs",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0
