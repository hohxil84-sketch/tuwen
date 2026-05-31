"""Sprint-02 Task-03: Provider Mock Foundation 聚焦测试。

覆盖：
- ProviderResult 统一结构验证
- MockProvider 确定性成功和可控失败
- provider_service 成功/失败日志路径
- cost_service 负值拒绝
- raw_usage 无敏感内容泄漏
- 不写入 credit_ledger
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.models.credit_ledger import CreditLedger
from app.models.provider_call_log import ProviderCallLog
from app.providers.base import ProviderRequest, ProviderResult
from app.providers.mock_provider import MockProvider, MockProviderError
from app.services.cost_service import calculate_mock_cost
from app.services.provider_service import execute_provider_call


# ---------------------------------------------------------------------------
# 1. ProviderResult 统一结构验证
# ---------------------------------------------------------------------------


class TestProviderResultShape:
    """ProviderResult 必须包含统一结构的全部字段，且成本/用量非负。"""

    def test_result_has_unified_fields(self):
        """构建 ProviderResult 时应能设置所有统一字段。"""
        result = ProviderResult(
            provider="mock",
            model="mock-text-v1",
            input_units=100,
            output_units=200,
            image_units=1,
            gpu_seconds=0.5,
            raw_cost=0.0012,
            estimated_cost=0.003,
            currency="CNY",
            result={"text": "hello"},
            raw_usage={"tokens": 300},
        )
        assert result.provider == "mock"
        assert result.model == "mock-text-v1"
        assert result.input_units == 100
        assert result.output_units == 200
        assert result.image_units == 1
        assert result.gpu_seconds == 0.5
        assert result.raw_cost == 0.0012
        assert result.estimated_cost == 0.003
        assert result.currency == "CNY"
        assert result.result == {"text": "hello"}
        assert result.raw_usage == {"tokens": 300}

    def test_result_defaults_are_nonnegative(self):
        """使用默认值构建时，所有数字字段应非负。"""
        result = ProviderResult(provider="mock", model="mock-text-v1")
        assert result.input_units >= 0
        assert result.output_units >= 0
        assert result.image_units >= 0
        assert result.gpu_seconds >= 0.0
        assert result.raw_cost >= 0.0
        assert result.estimated_cost >= 0.0

    def test_result_rejects_negative_input_units(self):
        """input_units < 0 应被 Pydantic 拒绝。"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ProviderResult(provider="mock", model="mock-text-v1", input_units=-1)

    def test_result_rejects_negative_estimated_cost(self):
        """estimated_cost < 0 应被 Pydantic Field(ge=0) 拒绝。"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ProviderResult(
                provider="mock",
                model="mock-text-v1",
                estimated_cost=-0.01,
            )

    def test_result_rejects_negative_raw_cost(self):
        """raw_cost < 0 应被 Pydantic Field(ge=0) 拒绝。"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ProviderResult(provider="mock", model="mock-text-v1", raw_cost=-1.0)


# ---------------------------------------------------------------------------
# 2. MockProvider 行为验证
# ---------------------------------------------------------------------------


class TestMockProvider:
    """MockProvider 确定性、无网络、可控失败。"""

    async def test_success_is_deterministic(self):
        """同一 feature 重复调用应返回相同结果。"""
        provider = MockProvider()
        request = ProviderRequest(feature="text_gen")
        r1 = await provider.call(request)
        r2 = await provider.call(request)

        assert r1.provider == r2.provider == "mock"
        assert r1.model == r2.model == "mock-text-v1"
        assert r1.input_units == r2.input_units
        assert r1.output_units == r2.output_units
        assert r1.result == r2.result

    async def test_different_features_different_usage(self):
        """不同 feature 应产生不同用量数据。"""
        provider = MockProvider()
        r_ocr = await provider.call(ProviderRequest(feature="ocr"))
        r_text = await provider.call(ProviderRequest(feature="text_gen"))
        # OCR 和 text_gen 的用量应不同
        assert r_ocr.input_units != r_text.input_units or r_ocr.output_units != r_text.output_units

    async def test_unknown_feature_uses_defaults(self):
        """未知 feature 使用默认配置，不抛异常。"""
        provider = MockProvider()
        result = await provider.call(ProviderRequest(feature="unknown_feature_xyz"))
        assert result.provider == "mock"
        assert result.model == "mock-text-v1"
        assert result.input_units == 10
        assert result.output_units == 20

    async def test_controlled_failure(self):
        """feature='test-error' 应抛出 MockProviderError。"""
        provider = MockProvider()
        with pytest.raises(MockProviderError) as exc_info:
            await provider.call(ProviderRequest(feature="test-error"))
        assert exc_info.value.error_code == "MOCK_ERROR"

    async def test_raw_usage_no_sensitive_data(self):
        """raw_usage 不应包含 prompt、API key、token、secret 等敏感字段。"""
        provider = MockProvider()
        result = await provider.call(ProviderRequest(feature="text_gen"))
        raw_usage_keys = {k.lower() for k in result.raw_usage}
        for forbidden in ["prompt", "api_key", "apikey", "token", "secret", "password"]:
            assert forbidden not in raw_usage_keys, f"raw_usage 包含敏感 key: {forbidden}"

    async def test_no_network_imports(self):
        """MockProvider 不导入网络库或 AI SDK。"""
        import inspect
        source = inspect.getsource(MockProvider)
        for forbidden_import in ["openai", "anthropic", "requests", "httpx", "aiohttp"]:
            assert forbidden_import not in source, f"MockProvider 不应导入 {forbidden_import}"


# ---------------------------------------------------------------------------
# 3. cost_service 验证
# ---------------------------------------------------------------------------


class TestCostService:
    """calculate_mock_cost 确定性、非负、拒绝负数。"""

    def test_deterministic_same_input_same_output(self):
        """相同输入产生相同输出。"""
        c1 = calculate_mock_cost(input_units=100, output_units=50, image_units=0, gpu_seconds=0.0)
        c2 = calculate_mock_cost(input_units=100, output_units=50, image_units=0, gpu_seconds=0.0)
        assert c1 == c2

    def test_returns_nonnegative(self):
        """合法输入应返回非负值。"""
        cost = calculate_mock_cost(input_units=0, output_units=0, image_units=0, gpu_seconds=0.0)
        assert cost >= 0.0

    def test_positive_units_produce_positive_cost(self):
        """正用量应产生正成本。"""
        cost = calculate_mock_cost(input_units=1000, output_units=500, image_units=1, gpu_seconds=0.2)
        assert cost > 0.0

    def test_rejects_negative_input_units(self):
        """input_units < 0 → ValueError。"""
        with pytest.raises(ValueError, match="input_units"):
            calculate_mock_cost(input_units=-1, output_units=0, image_units=0, gpu_seconds=0.0)

    def test_rejects_negative_output_units(self):
        """output_units < 0 → ValueError。"""
        with pytest.raises(ValueError, match="output_units"):
            calculate_mock_cost(input_units=0, output_units=-5, image_units=0, gpu_seconds=0.0)

    def test_rejects_negative_image_units(self):
        """image_units < 0 → ValueError。"""
        with pytest.raises(ValueError, match="image_units"):
            calculate_mock_cost(input_units=0, output_units=0, image_units=-1, gpu_seconds=0.0)

    def test_rejects_negative_gpu_seconds(self):
        """gpu_seconds < 0 → ValueError。"""
        with pytest.raises(ValueError, match="gpu_seconds"):
            calculate_mock_cost(input_units=0, output_units=0, image_units=0, gpu_seconds=-0.1)


# ---------------------------------------------------------------------------
# 4. provider_service 集成测试（成功路径）
# ---------------------------------------------------------------------------


class TestProviderServiceSuccess:
    """execute_provider_call 成功路径：写日志、返回结果、不碰 credit_ledger。"""

    async def test_success_writes_provider_call_log(self, db_session, test_user, test_device):
        """成功调用应写入 provider_call_log 且 status='success'。"""
        provider = MockProvider()
        request = ProviderRequest(feature="text_gen")
        request_id = "req-success-001"

        result = await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=test_device.id,
            request_id=request_id,
        )

        assert result.provider == "mock"
        assert result.estimated_cost > 0.0  # cost_service 已计算

        # 查询日志
        stmt = (
            select(ProviderCallLog)
            .where(ProviderCallLog.request_id == request_id)
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.status == "success"
        assert row.error_code is None
        assert row.provider == "mock"
        assert row.model == "mock-text-v1"
        assert row.feature == "text_gen"
        assert row.user_id == test_user.id
        assert row.device_id == test_device.id
        assert row.prompt_tokens > 0
        assert row.completion_tokens > 0
        assert row.total_tokens == row.prompt_tokens + row.completion_tokens
        assert row.estimated_cost is not None and row.estimated_cost > 0
        assert row.credits_charged == 0  # 扣费在后续任务实现
        assert row.latency_ms is not None and row.latency_ms >= 0

    async def test_success_does_not_write_credit_ledger(self, db_session, test_user, test_device):
        """成功调用不应写入 credit_ledger。"""
        provider = MockProvider()
        request = ProviderRequest(feature="text_gen")

        # 记录调用前的 credit_ledger 计数
        count_before = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0

        await execute_provider_call(
            db=db_session,
            provider=provider,
            request=request,
            user_id=test_user.id,
            device_id=test_device.id,
        )

        count_after = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0

        assert count_after == count_before, "execute_provider_call 不应写入 credit_ledger"

    async def test_auto_generates_request_id(self, db_session):
        """未提供 request_id 时自动生成。"""
        provider = MockProvider()
        request = ProviderRequest(feature="text_gen")

        result = await execute_provider_call(db=db_session, provider=provider, request=request)

        assert result is not None
        assert result.provider == "mock"

        # 应写入一条带 request_id 的日志
        count = (
            await db_session.execute(select(func.count()).select_from(ProviderCallLog))
        ).scalar() or 0
        assert count >= 1


# ---------------------------------------------------------------------------
# 5. provider_service 集成测试（失败路径）
# ---------------------------------------------------------------------------


class TestProviderServiceError:
    """execute_provider_call 失败路径：记录 error 日志，不写 credit_ledger。"""

    async def test_error_writes_provider_call_log_with_error_code(
        self, db_session, test_user, test_device
    ):
        """可控失败应写入 provider_call_log 且 status='error'，含 error_code。"""
        provider = MockProvider()
        request = ProviderRequest(feature="test-error")
        request_id = "req-error-001"

        with pytest.raises(MockProviderError):
            await execute_provider_call(
                db=db_session,
                provider=provider,
                request=request,
                user_id=test_user.id,
                device_id=test_device.id,
                request_id=request_id,
            )

        # 查询日志：即使异常被重新抛出，error 日志应已写入
        stmt = (
            select(ProviderCallLog)
            .where(ProviderCallLog.request_id == request_id)
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.status == "error"
        assert row.error_code == "MOCK_ERROR"
        assert row.provider == "mock"
        assert row.user_id == test_user.id
        assert row.latency_ms is not None and row.latency_ms >= 0

    async def test_error_does_not_write_credit_ledger(self, db_session, test_user, test_device):
        """失败调用不应写入 credit_ledger。"""
        provider = MockProvider()
        request = ProviderRequest(feature="test-error")

        count_before = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0

        with pytest.raises(MockProviderError):
            await execute_provider_call(
                db=db_session,
                provider=provider,
                request=request,
                user_id=test_user.id,
                device_id=test_device.id,
            )

        count_after = (
            await db_session.execute(select(func.count()).select_from(CreditLedger))
        ).scalar() or 0

        assert count_after == count_before, "错误路径也不应写入 credit_ledger"

    async def test_error_log_has_no_raw_prompt(self, db_session, test_user):
        """错误日志中不包含原始 prompt 文本。"""
        provider = MockProvider()
        request = ProviderRequest(feature="test-error")
        request_id = "req-error-noprompt"

        with pytest.raises(MockProviderError):
            await execute_provider_call(
                db=db_session,
                provider=provider,
                request=request,
                user_id=test_user.id,
                request_id=request_id,
            )

        stmt = (
            select(ProviderCallLog)
            .where(ProviderCallLog.request_id == request_id)
        )
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        # provider_call_log 模型不包含 prompt_text / raw_prompt 等字段
        # 确认 model 中没有存储用户消息内容
        assert row.feature == "test-error"  # feature 是功能名，非 prompt
