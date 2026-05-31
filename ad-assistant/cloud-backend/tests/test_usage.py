"""Usage event API tests — table structure, write, query, auth, isolation, metadata sanitization."""

import uuid

import pytest

from app.core.security import create_access_token
from app.models.usage_event import UsageEvent
from app.models.user import User
from app.services.usage_service import (
    _sanitize_metadata,
    list_usage_events,
    record_usage_event,
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


class TestUsageEventTable:
    """usage_events 表结构和列验证."""

    async def test_table_exists(self, db_session):
        """usage_events 表应存在且可通过 ORM 查询."""
        result = await db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='usage_events'"
            )
        )
        row = result.scalar_one_or_none()
        assert row == "usage_events"

    async def test_columns_match_schema(self, db_session):
        """确认表包含所有必需列."""
        result = await db_session.execute(
            __import__("sqlalchemy").text("PRAGMA table_info('usage_events')")
        )
        columns = {row[1] for row in result.fetchall()}
        required = {
            "id", "user_id", "device_id", "event_type", "feature",
            "request_id", "metadata_json", "created_at",
        }
        assert required.issubset(columns)


# ---------------------------------------------------------------------------
# 2. Metadata 清洗单元测试（不依赖 DB）
# ---------------------------------------------------------------------------


class TestMetadataSanitizer:
    """_sanitize_metadata 白名单 + 递归敏感信息拦截."""

    def test_none_returns_none(self):
        """None 输入返回 None."""
        assert _sanitize_metadata(None) is None

    def test_non_dict_returns_none(self):
        """非 dict 输入返回 None."""
        assert _sanitize_metadata("bad") is None  # type: ignore[arg-type]
        assert _sanitize_metadata([1, 2, 3]) is None  # type: ignore[arg-type]

    def test_allowlisted_keys_preserved(self):
        """白名单 key 的值原样保留."""
        meta = {"image_count": 3, "source": "desktop", "duration_ms": 120}
        result = _sanitize_metadata(meta)
        assert result == meta

    def test_non_allowlisted_keys_dropped(self):
        """非白名单 key 被丢弃."""
        meta = {
            "image_count": 2,       # 白名单 → 保留
            "prompt": "hello",       # 不在白名单 → 丢弃
            "user_email": "a@b.c",   # 不在白名单 → 丢弃
            "raw_text": "secret",    # 不在白名单 → 丢弃
        }
        result = _sanitize_metadata(meta)
        assert result == {"image_count": 2}

    def test_sensitive_string_value_redacted(self):
        """白名单 key 但 value 包含敏感模式 → 替换为 [REDACTED]."""
        meta = {
            "source": "my_api_key_12345",  # value 含 "api_key" 模式
            "format": "bearer_token_xxx",   # value 含 "bearer" 模式
            "engine": "no-sensitive-here",  # 安全 value
        }
        result = _sanitize_metadata(meta)
        assert result == {
            "source": "[REDACTED]",
            "format": "[REDACTED]",
            "engine": "no-sensitive-here",
        }

    def test_nested_dict_sanitized(self):
        """嵌套 dict 递归清洗."""
        meta = {
            "image_count": 5,
            "source": {
                "mode": "auto",           # 白名单 → 保留
                "api_key": "sk-12345",    # 不在白名单 → 丢弃
                "token": "Bearer xyz",    # 不在白名单 → 丢弃
            },
        }
        result = _sanitize_metadata(meta)
        assert result == {
            "image_count": 5,
            "source": {"mode": "auto"},
        }

    def test_nested_list_sanitized(self):
        """嵌套 list 递归清洗."""
        meta = {
            "image_count": 2,
            "source": [
                {"mode": "auto", "secret": "xxx"},   # secret 丢弃
                {"mode": "manual", "password": "yyy"},  # password 丢弃
            ],
        }
        result = _sanitize_metadata(meta)
        assert result == {
            "image_count": 2,
            "source": [
                {"mode": "auto"},
                {"mode": "manual"},
            ],
        }

    def test_nested_list_string_redacted(self):
        """列表中的字符串值也会被检查."""
        meta = {
            "source": ["normal", "contains_token_123", "also_fine"],
        }
        result = _sanitize_metadata(meta)
        assert result == {
            "source": ["normal", "[REDACTED]", "also_fine"],
        }

    def test_all_keys_dropped_returns_none(self):
        """所有 key 都被丢弃 → 返回 None."""
        meta = {
            "prompt": "hello world",
            "api_key": "sk-deadbeef",
            "secret_token": "xyz",
        }
        result = _sanitize_metadata(meta)
        assert result is None

    def test_sensitive_key_names_dropped(self):
        """包含敏感模式的 key 名（即便不在白名单）被丢弃（双重保护）."""
        # 这些 key 本来就不在白名单，但额外验证它们确实被丢弃
        meta = {
            "api_key": "value1",
            "bearer_token": "value2",
            "password": "value3",
            "authorization": "value4",
            "secret_key": "value5",
        }
        result = _sanitize_metadata(meta)
        assert result is None  # 全部被丢弃


# ---------------------------------------------------------------------------
# 3. 写入测试（含真实敏感 metadata）
# ---------------------------------------------------------------------------


class TestUsageEventWrite:
    """使用 service 层写入 usage_events."""

    async def test_record_usage_event_success(self, db_session, test_user, test_device):
        """record_usage_event 应成功写入一条安全记录."""
        result = await record_usage_event(
            db=db_session,
            event_type="OCR_LOCAL",
            feature="ocr",
            user_id=test_user.id,
            device_id=test_device.id,
            request_id="req_test_001",
            metadata={"image_count": 1},
        )
        assert "id" in result
        assert result["event_type"] == "OCR_LOCAL"
        assert result["feature"] == "ocr"

        # 确认已持久化
        stmt = __import__("sqlalchemy").select(UsageEvent).where(
            UsageEvent.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.event_type == "OCR_LOCAL"

    async def test_sensitive_metadata_stripped_on_write(self, db_session, test_user):
        """传入含 API Key / Token / password 的 metadata，应被清洗后落盘."""
        result = await record_usage_event(
            db=db_session,
            event_type="SENSITIVE_TEST",
            feature="ocr",
            user_id=test_user.id,
            metadata={
                "image_count": 3,
                "api_key": "sk-evil-deadbeef",           # 非白名单 → 丢弃
                "bearer_token": "Bearer xyz789",          # 非白名单 → 丢弃
                "password": "super-secret",               # 非白名单 → 丢弃
                "source": "my_token_is_leaked",           # 白名单但 value 含敏感 → REDACTED
                "raw_prompt": "tell me a joke",           # 非白名单 → 丢弃
                "secret": "classified",                   # 非白名单 → 丢弃
                "engine": "paddleocr",                    # 白名单安全值 → 保留
                "duration_ms": 450,                       # 白名单安全值 → 保留
            },
        )
        assert "id" in result

        # 验证落盘内容
        stmt = __import__("sqlalchemy").select(UsageEvent).where(
            UsageEvent.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.metadata_json is not None

        meta = row.metadata_json
        # 白名单 key 保留
        assert meta["image_count"] == 3
        assert meta["engine"] == "paddleocr"
        assert meta["duration_ms"] == 450
        # 敏感 value 被 REDACTED
        assert meta["source"] == "[REDACTED]"
        # 非白名单 key 被丢弃
        assert "api_key" not in meta
        assert "bearer_token" not in meta
        assert "password" not in meta
        assert "raw_prompt" not in meta
        assert "secret" not in meta

    async def test_all_sensitive_metadata_stripped_returns_none(self, db_session, test_user):
        """全部 metadata 被清洗 → metadata_json 为 None."""
        result = await record_usage_event(
            db=db_session,
            event_type="ALL_SENSITIVE",
            feature="ocr",
            user_id=test_user.id,
            metadata={
                "api_key": "sk-abc",
                "token": "tok-123",
                "password": "hunter2",
                "secret": "classified",
                "authorization": "Bearer xxx",
            },
        )
        stmt = __import__("sqlalchemy").select(UsageEvent).where(
            UsageEvent.id == uuid.UUID(result["id"])
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.metadata_json is None


# ---------------------------------------------------------------------------
# 4. 查询鉴权测试
# ---------------------------------------------------------------------------


class TestUsageEventAuth:
    """usage_events 查询鉴权."""

    async def test_no_auth_returns_401(self, client):
        """无 token → 401."""
        res = await client.get("/api/v1/usage/events")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_user_cannot_access_other_user_data(
        self, client, db_session, test_user, test_device
    ):
        """用户 A 不能查询用户 B 的使用事件."""
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

        # 为用户 A 写入一条记录
        await record_usage_event(
            db=db_session,
            event_type="OCR_LOCAL",
            feature="ocr",
            user_id=test_user.id,
            device_id=test_device.id,
        )

        # 为用户 B 写入一条记录
        await record_usage_event(
            db=db_session,
            event_type="VECTORIZE",
            feature="vectorize",
            user_id=user_b.id,
        )

        # 用 test_user 的身份查询 — 应该只能看到自己的数据
        res = await client.get(
            "/api/v1/usage/events",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        # 所有返回的记录都应属于 test_user
        for item in body["data"]["items"]:
            assert item["user_id"] == str(test_user.id)


# ---------------------------------------------------------------------------
# 5. 查询功能测试
# ---------------------------------------------------------------------------


class TestUsageEventQuery:
    """使用事件查询功能测试."""

    async def test_pagination(self, client, db_session, test_user, test_device):
        """分页查询：limit 和 offset 生效."""
        # 写入 3 条记录
        for i in range(3):
            await record_usage_event(
                db=db_session,
                event_type=f"EVENT_{i}",
                feature="ocr",
                user_id=test_user.id,
                device_id=test_device.id,
            )

        # limit=2
        res = await client.get(
            "/api/v1/usage/events?limit=2&offset=0",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["limit"] == 2
        assert body["data"]["offset"] == 0
        assert len(body["data"]["items"]) == 2
        assert body["data"]["total"] >= 3

    async def test_feature_filter(self, client, db_session, test_user, test_device):
        """按 feature 筛选."""
        # 写入不同 feature 的记录
        await record_usage_event(
            db=db_session,
            event_type="OCR_LOCAL",
            feature="ocr",
            user_id=test_user.id,
            device_id=test_device.id,
        )
        await record_usage_event(
            db=db_session,
            event_type="VECTORIZE",
            feature="vectorize",
            user_id=test_user.id,
            device_id=test_device.id,
        )

        # 按 feature=ocr 筛选
        res = await client.get(
            "/api/v1/usage/events?feature=ocr",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        for item in body["data"]["items"]:
            assert item["feature"] == "ocr"

    async def test_empty_list_for_new_user(self, client, test_user, test_device):
        """新用户应返回空列表."""
        res = await client.get(
            "/api/v1/usage/events",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0
