"""Mock AI API tests — Sprint-02 Task-04.

覆盖：
- 未鉴权 → 401
- 成功调用 → 200 + 统一 wrapper
- 响应不暴露 raw_usage
- request_id 传播到 response 和 provider_call_log
- provider_call_log 写入正确字段
- credit_ledger 无写入
- 输入校验拒绝空/超长字段
- 禁用设备 / 被封设备 → 403
"""

import uuid

import pytest
from sqlalchemy import select, text

from app.core.security import create_access_token
from app.models.credit_account import CreditAccount
from app.models.credit_ledger import CreditLedger
from app.models.provider_call_log import ProviderCallLog


# ---------------------------------------------------------------------------
# Ensure mock_ad_copy/standard routes to MockProvider during API tests.
# DeepSeek routing is tested separately in test_deepseek_provider.py.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _route_mock_ad_copy_standard_to_mock():
    """Override routing so mock_ad_copy/standard → mock during API tests."""
    from app.providers.router import DEFAULT_ROUTING_RULES

    original = DEFAULT_ROUTING_RULES["mock_ad_copy"]["standard"]
    DEFAULT_ROUTING_RULES["mock_ad_copy"]["standard"] = "mock"
    # Reset module-level router singleton so it picks up the new rule
    import app.providers.router as _router_mod

    _cached_router = _router_mod._router
    _router_mod._router = None
    yield
    DEFAULT_ROUTING_RULES["mock_ad_copy"]["standard"] = original
    _router_mod._router = _cached_router


@pytest.fixture
async def _fund_test_user(db_session, test_user):
    """Give test_user enough credits to pass pre-flight balance check."""
    account = CreditAccount(
        user_id=test_user.id, plan_code="standard", monthly_grant=0,
        balance=100, status="active",
    )
    db_session.add(account)
    await db_session.flush()
    return account


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


ENDPOINT = "/api/v1/mock-ai/ad-copy"

VALID_BODY = {
    "product_name": "A4 poster printing",
    "selling_points": ["same-day pickup", "waterproof material"],
    "platform": "douyin",
    "tone": "direct",
}


# ---------------------------------------------------------------------------
# 1. 鉴权测试
# ---------------------------------------------------------------------------


class TestMockAiAuth:
    """未鉴权 / 鉴权失败场景."""

    async def test_no_auth_returns_401(self, client):
        """无 Authorization header → 401."""
        res = await client.post(ENDPOINT, json=VALID_BODY)
        assert res.status_code == 401, res.text
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "AUTH_REQUIRED"

    async def test_invalid_token_returns_401(self, client):
        """无效 Bearer token → 401."""
        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert res.status_code == 401, res.text
        assert res.json()["error"]["code"] == "AUTH_REQUIRED"

    async def test_disabled_user_returns_403(self, client, db_session, test_device):
        """status=disabled 的用户 → 403."""
        from app.models.user import User
        from app.core.security import hash_password

        disabled_user = User(
            id=uuid.uuid4(),
            account="disabled-user@example.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="disabled",
        )
        db_session.add(disabled_user)
        await db_session.flush()

        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(disabled_user, test_device),
        )
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "USER_DISABLED"


# ---------------------------------------------------------------------------
# 2. 成功响应测试
# ---------------------------------------------------------------------------


class TestMockAiSuccess:
    """成功调用 → 200 + 统一 wrapper."""

    async def test_success_returns_unified_wrapper(
        self, client, test_user, test_device, _fund_test_user,
    ):
        """成功调用应返回 {success, data, error, request_id}."""
        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["error"] is None
        assert "request_id" in body
        assert body["request_id"].startswith("req_")

    async def test_response_data_has_required_fields(
        self, client, test_user, test_device, _fund_test_user,
    ):
        """响应 data 包含 feature/provider/model/text/estimated_cost/credits_charged."""
        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        body = res.json()
        data = body["data"]
        assert data["feature"] == "mock_ad_copy"
        assert data["provider"] == "mock"
        assert data["model"] == "mock-text-v1"
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0
        assert data["estimated_cost"] >= 0.0
        # Sprint-03 Task-03: real credit deduction → credits_charged > 0
        assert data["credits_charged"] == 2  # mock default usage ~2 credits

    async def test_response_does_not_expose_raw_usage(
        self, client, test_user, test_device, _fund_test_user,
    ):
        """响应 data 中不得包含 raw_usage."""
        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        data = res.json()["data"]
        assert "raw_usage" not in data


# ---------------------------------------------------------------------------
# 3. provider_call_log 写入测试
# ---------------------------------------------------------------------------


class TestMockAiProviderLog:
    """成功调用写入 provider_call_log 且不写 credit_ledger."""

    async def test_writes_provider_call_log_success_row(
        self, client, db_session, test_user, test_device, _fund_test_user,
    ):
        """成功调用应在 provider_call_log 中写入一行 status=success."""
        # 调用前的记录数
        count_before = (
            await db_session.execute(
                select(ProviderCallLog).where(
                    ProviderCallLog.user_id == test_user.id,
                )
            )
        ).scalars().all()

        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200

        # 调用后的记录
        rows_after = (
            await db_session.execute(
                select(ProviderCallLog).where(
                    ProviderCallLog.user_id == test_user.id,
                )
            )
        ).scalars().all()

        assert len(rows_after) == len(count_before) + 1
        row = rows_after[-1]
        assert row.status == "success"
        assert row.feature == "mock_ad_copy"
        assert row.provider == "mock"
        assert row.model == "mock-text-v1"
        assert row.user_id == test_user.id
        assert row.device_id == test_device.id
        # Sprint-03 Task-03: real deduction → credits_charged > 0
        assert row.credits_charged == 2  # mock default usage ~2 credits
        assert row.error_code is None

    async def test_credit_ledger_row_created_by_deduction(
        self, client, db_session, test_user, test_device, _fund_test_user,
    ):
        """Sprint-03: 成功调用后 credit_ledger 记录 consume 流水."""
        count_before = (
            await db_session.execute(
                select(CreditLedger).where(
                    CreditLedger.user_id == test_user.id,
                )
            )
        ).scalars().all()

        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200

        count_after = (
            await db_session.execute(
                select(CreditLedger).where(
                    CreditLedger.user_id == test_user.id,
                )
            )
        ).scalars().all()

        # Now credit_ledger IS written (real deduction since S03-T03)
        assert len(count_after) == len(count_before) + 1
        ledger_entry = count_after[-1]
        assert ledger_entry.change_type == "consume"
        assert ledger_entry.source_type == "provider_call"


# ---------------------------------------------------------------------------
# 4. request_id 传播测试
# ---------------------------------------------------------------------------


class TestMockAiRequestId:
    """X-Request-ID 传播到 response 和 provider_call_log."""

    async def test_request_id_propagates_to_response(
        self, client, test_user, test_device, _fund_test_user,
    ):
        """自定义 X-Request-ID → response.request_id 与之匹配."""
        custom_rid = "req-custom-test-123"
        headers = _auth_header(test_user, test_device)
        headers["X-Request-ID"] = custom_rid

        res = await client.post(ENDPOINT, json=VALID_BODY, headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["request_id"] == custom_rid

    async def test_request_id_propagates_to_provider_call_log(
        self, client, db_session, test_user, test_device, _fund_test_user,
    ):
        """自定义 X-Request-ID → provider_call_log.request_id 与之匹配."""
        custom_rid = "req-log-propagation-456"
        headers = _auth_header(test_user, test_device)
        headers["X-Request-ID"] = custom_rid

        res = await client.post(ENDPOINT, json=VALID_BODY, headers=headers)
        assert res.status_code == 200

        rows = (
            await db_session.execute(
                select(ProviderCallLog).where(
                    ProviderCallLog.request_id == custom_rid,
                )
            )
        ).scalars().all()

        assert len(rows) == 1
        assert rows[0].request_id == custom_rid

    async def test_auto_generated_request_id_propagates(
        self, client, db_session, test_user, test_device, _fund_test_user,
    ):
        """无 X-Request-ID → middleware 自动生成，response 与 provider log 一致."""
        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        rid = body["request_id"]
        assert rid.startswith("req_")

        # provider_call_log 中的 request_id 应与 response 一致
        rows = (
            await db_session.execute(
                select(ProviderCallLog).where(
                    ProviderCallLog.request_id == rid,
                )
            )
        ).scalars().all()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# 5. 输入校验测试
# ---------------------------------------------------------------------------


class TestMockAiValidation:
    """请求校验拒绝空/超长输入."""

    async def test_empty_product_name_rejected(self, client, test_user, test_device):
        """product_name 为空 → 422."""
        body = {**VALID_BODY, "product_name": ""}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_missing_product_name_rejected(self, client, test_user, test_device):
        """缺少 product_name → 422."""
        body = {**VALID_BODY}
        del body["product_name"]
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_oversized_product_name_rejected(self, client, test_user, test_device):
        """product_name 超过 200 字符 → 422."""
        body = {**VALID_BODY, "product_name": "A" * 201}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text

    async def test_too_many_selling_points_rejected(self, client, test_user, test_device):
        """selling_points 超过 5 条 → 422."""
        body = {**VALID_BODY, "selling_points": [f"point{i}" for i in range(6)]}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text

    async def test_oversized_selling_point_item_rejected(self, client, test_user, test_device):
        """selling_point 单项超过 200 字符 → 422."""
        body = {**VALID_BODY, "selling_points": ["ok", "B" * 201]}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text

    async def test_oversized_platform_rejected(self, client, test_user, test_device):
        """platform 超过 50 字符 → 422."""
        body = {**VALID_BODY, "platform": "P" * 51}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text

    async def test_oversized_tone_rejected(self, client, test_user, test_device):
        """tone 超过 50 字符 → 422."""
        body = {**VALID_BODY, "tone": "T" * 51}
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 422, res.text


# ---------------------------------------------------------------------------
# 6. 设备状态测试
# ---------------------------------------------------------------------------


class TestMockAiDevice:
    """设备被封 / 未绑定场景."""

    async def test_banned_device_returns_403(self, client, db_session, test_user):
        """设备 status=banned → 403 DEVICE_BANNED."""
        from app.models.device import Device
        import hashlib

        fp = hashlib.sha256(b"banned-device-fp").hexdigest()
        banned_device = Device(
            id=uuid.uuid4(),
            user_id=test_user.id,
            device_fingerprint_hash=fp,
            device_name="Banned Device",
            status="banned",
        )
        db_session.add(banned_device)
        await db_session.flush()

        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, banned_device),
        )
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "DEVICE_BANNED"

    async def test_device_not_bound_to_user_returns_403(self, client, db_session, test_user, test_device):
        """token 中 device 不属于当前用户 → 403."""
        # 创建另一个用户和其设备
        from app.models.user import User
        from app.core.security import hash_password

        other_user = User(
            id=uuid.uuid4(),
            account="other@example.com",
            password_hash=hash_password("pw"),
            plan_code="standard",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        # 用 test_user 的 token 但 device_id 指向 other_user 的设备
        # 这种情况在 deps 中会被检测到：device.user_id != user.id
        import hashlib
        from app.models.device import Device

        fp = hashlib.sha256(b"other-device-fp").hexdigest()
        other_device = Device(
            id=uuid.uuid4(),
            user_id=other_user.id,  # 属于 other_user
            device_fingerprint_hash=fp,
            device_name="Other Device",
            status="active",
        )
        db_session.add(other_device)
        await db_session.flush()

        res = await client.post(
            ENDPOINT,
            json=VALID_BODY,
            headers=_auth_header(test_user, other_device),
        )
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "DEVICE_NOT_BOUND"


# ---------------------------------------------------------------------------
# 7. 客户端不可提交敏感字段
# ---------------------------------------------------------------------------


class TestMockAiNoClientControl:
    """验证响应字段由后端决定，客户端不可覆盖."""

    async def test_client_cannot_submit_provider_cost_or_credits(
        self, client, test_user, test_device, _fund_test_user,
    ):
        """请求中包含额外字段不应影响后端计算的值."""
        body = {
            **VALID_BODY,
            "provider": "deepseek",       # 客户端不应提交
            "model": "deepseek-chat",     # 客户端不应提交
            "estimated_cost": 999.0,      # 客户端不应提交
            "credits_charged": 999,       # 客户端不应提交
            "user_id": "fake",            # 客户端不应提交
            "device_id": "fake",          # 客户端不应提交
            "request_id": "fake",         # 客户端不应提交
        }
        res = await client.post(
            ENDPOINT,
            json=body,
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        # 后端决定的值不应被客户端提交覆盖
        assert data["provider"] == "mock"
        assert data["model"] == "mock-text-v1"
        # Sprint-03 Task-03: real deduction → credits_charged > 0
        assert data["credits_charged"] == 2  # mock default usage ~2 credits
        assert data["estimated_cost"] >= 0.0
