"""Sprint-03 Task-02: DeepSeekProvider 聚焦测试。

覆盖：
- 成功路径：正常响应 → ProviderResult 映射
- 错误路径：API key missing / auth error / rate limit / timeout / empty response
- raw_usage 安全性：不包含 prompt 文本
- calculate_deepseek_cost：定价计算正确、拒绝负数
- 集成：路由规则 mock_ad_copy/standard → deepseek

所有测试 mock openai.AsyncOpenAI，不发起真实网络请求。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.base import ProviderRequest
from app.providers.deepseek_provider import DeepSeekProvider, DeepSeekProviderError
from app.providers.registry import get_provider_registry
from app.providers.router import get_provider_router
from app.services.cost_service import calculate_deepseek_cost


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_mock_chat_completion(content: str, prompt_tokens: int, completion_tokens: int, model: str = "deepseek-chat", finish_reason: str = "stop"):
    """Build a minimal mock ChatCompletion object for testing."""

    resp = MagicMock()
    resp.model = model
    resp.choices = [
        MagicMock(
            finish_reason=finish_reason,
            message=MagicMock(content=content),
        )
    ]
    resp.usage = MagicMock(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return resp


def _make_mock_httpx_response(status_code: int = 200):
    """Build a minimal httpx.Response mock for OpenAI exception constructors."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"x-request-id": "test-req-123"}
    resp.request = MagicMock()
    return resp


def _make_provider_request(message: str = "你好，请写一段广告文案。") -> ProviderRequest:
    return ProviderRequest(feature="mock_ad_copy", message=message)


# ---------------------------------------------------------------------------
# 1. 成功路径
# ---------------------------------------------------------------------------


class TestDeepSeekProviderSuccess:
    """正常调用路径测试。"""

    @pytest.mark.asyncio
    async def test_call_returns_provider_result(self):
        """正常调用返回 ProviderResult，字段映射正确。"""
        provider = DeepSeekProvider()
        mock_response = _make_mock_chat_completion(
            content="这是一段广告文案。",
            prompt_tokens=100,
            completion_tokens=200,
        )

        with patch.object(provider, "_client", new_callable=lambda: None):
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            # Bypass _get_client
            provider._client = mock_client

            result = await provider.call(_make_provider_request())

        assert result.provider == "deepseek"
        assert result.model == "deepseek-chat"
        assert result.input_units == 100
        assert result.output_units == 200
        assert result.image_units == 0
        assert result.gpu_seconds == 0.0
        assert result.currency == "CNY"
        assert result.result["text"] == "这是一段广告文案。"

    @pytest.mark.asyncio
    async def test_raw_usage_excludes_prompt_text(self):
        """raw_usage 不包含原始 prompt 文本。"""
        provider = DeepSeekProvider()
        mock_response = _make_mock_chat_completion(
            content="广告文案。",
            prompt_tokens=50,
            completion_tokens=50,
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        result = await provider.call(_make_provider_request(message="产品：XX洗发水"))

        ru = result.raw_usage
        # 只包含安全的元数据
        assert "model" in ru
        assert "finish_reason" in ru
        assert "prompt_tokens" in ru
        assert "completion_tokens" in ru
        assert "total_tokens" in ru
        # 不包含任何用户内容
        raw_usage_str = str(ru)
        assert "XX洗发水" not in raw_usage_str
        assert "prompt" not in ru or ru.get("prompt") is None

    @pytest.mark.asyncio
    async def test_result_has_no_raw_prompt(self):
        """ProviderResult.result 也不应泄漏原始 prompt（只返回 AI 生成文本）。"""
        provider = DeepSeekProvider()
        mock_response = _make_mock_chat_completion(
            content="生成的文案。",
            prompt_tokens=30,
            completion_tokens=60,
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        result = await provider.call(_make_provider_request(message="写文案：去屑洗发水"))

        # result.result 只应包含 AI 生成的内容
        assert "去屑洗发水" not in str(result.result)
        assert result.result["text"] == "生成的文案。"


# ---------------------------------------------------------------------------
# 2. 错误路径
# ---------------------------------------------------------------------------


class TestDeepSeekProviderErrors:
    """错误处理路径测试。"""

    @pytest.mark.asyncio
    async def test_api_key_missing_raises(self):
        """未配置 API Key 时应抛出 API_KEY_MISSING 错误。"""
        provider = DeepSeekProvider()
        # 确保 _client 为 None 且 settings 中无 API key
        provider._client = None

        with patch("app.providers.deepseek_provider.settings") as mock_settings:
            mock_settings.DEEPSEEK_API_KEY = ""
            mock_settings.DEEPSEEK_BASE_URL = "https://api.deepseek.com"

            with pytest.raises(DeepSeekProviderError) as exc_info:
                await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "API_KEY_MISSING"

    @pytest.mark.asyncio
    async def test_auth_error_mapped(self):
        """认证失败（401）应映射为 AUTH_ERROR。"""
        import openai

        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.AuthenticationError(
                message="Invalid API key",
                response=_make_mock_httpx_response(401),
                body=None,
            )
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "AUTH_ERROR"

    @pytest.mark.asyncio
    async def test_rate_limit_mapped(self):
        """频率限制（429）应映射为 RATE_LIMITED。"""
        import openai

        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError(
                message="Rate limit exceeded",
                response=_make_mock_httpx_response(429),
                body=None,
            )
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "RATE_LIMITED"

    @pytest.mark.asyncio
    async def test_timeout_mapped(self):
        """超时应映射为 TIMEOUT。"""
        import openai

        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=None)
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_connection_error_mapped(self):
        """连接失败应映射为 CONNECTION_ERROR。"""
        import openai

        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=None)
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "CONNECTION_ERROR"

    @pytest.mark.asyncio
    async def test_bad_request_mapped(self):
        """请求格式错误（400）应映射为 BAD_REQUEST。"""
        import openai

        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.BadRequestError(
                message="Invalid request",
                response=_make_mock_httpx_response(400),
                body=None,
            )
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "BAD_REQUEST"

    @pytest.mark.asyncio
    async def test_empty_response_raises(self):
        """DeepSeek 返回空 choices 应抛出 EMPTY_RESPONSE。"""
        provider = DeepSeekProvider()

        class _EmptyResponse:
            model = "deepseek-chat"
            usage = None
            choices = []

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_EmptyResponse())
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "EMPTY_RESPONSE"

    @pytest.mark.asyncio
    async def test_unexpected_error_mapped(self):
        """非 OpenAI 异常应映射为 UNKNOWN_ERROR。"""
        provider = DeepSeekProvider()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("something went wrong")
        )
        provider._client = mock_client

        with pytest.raises(DeepSeekProviderError) as exc_info:
            await provider.call(_make_provider_request())

        assert exc_info.value.error_code == "UNKNOWN_ERROR"


# ---------------------------------------------------------------------------
# 3. 成本计算
# ---------------------------------------------------------------------------


class TestDeepSeekCost:
    """DeepSeek 官方定价计算。"""

    def test_pricing_zero_tokens(self):
        """零 token 成本应为 0。"""
        assert calculate_deepseek_cost(input_units=0, output_units=0) == 0.0

    def test_pricing_input_only(self):
        """纯输入 token 成本。"""
        # 1M input tokens = ¥1.00
        cost = calculate_deepseek_cost(input_units=1_000_000, output_units=0)
        assert cost == 1.0

    def test_pricing_output_only(self):
        """纯输出 token 成本。"""
        # 1M output tokens = ¥2.00
        cost = calculate_deepseek_cost(input_units=0, output_units=1_000_000)
        assert cost == 2.0

    def test_pricing_mixed(self):
        """混合 input/output 成本。"""
        # 500k input (¥0.50) + 500k output (¥1.00) = ¥1.50
        cost = calculate_deepseek_cost(input_units=500_000, output_units=500_000)
        assert cost == 1.50

    def test_pricing_small_tokens(self):
        """极小 token 数量仍返回非零值。"""
        cost = calculate_deepseek_cost(input_units=1, output_units=1)
        assert cost > 0
        # 1/1M * 1 + 1/1M * 2 = 0.000003
        assert cost == round(1 / 1_000_000 * 1 + 1 / 1_000_000 * 2, 8)

    def test_rejects_negative_input(self):
        """拒绝负数 input_units。"""
        with pytest.raises(ValueError, match="input_units"):
            calculate_deepseek_cost(input_units=-1, output_units=0)

    def test_rejects_negative_output(self):
        """拒绝负数 output_units。"""
        with pytest.raises(ValueError, match="output_units"):
            calculate_deepseek_cost(input_units=0, output_units=-1)


# ---------------------------------------------------------------------------
# 4. 集成：路由规则
# ---------------------------------------------------------------------------


class TestDeepSeekRouting:
    """验证 mock_ad_copy + standard 路由到 deepseek。"""

    @pytest.mark.asyncio
    async def test_routing_mock_ad_copy_standard_to_deepseek(self):
        """mock_ad_copy + standard → deepseek。"""
        router = get_provider_router()
        provider = await router.route("mock_ad_copy", "standard")
        assert isinstance(provider, DeepSeekProvider)

    @pytest.mark.asyncio
    async def test_routing_mock_ad_copy_expert_stays_mock(self):
        """mock_ad_copy + expert → mock（未改动）。"""
        from app.providers.mock_provider import MockProvider

        router = get_provider_router()
        provider = await router.route("mock_ad_copy", "expert")
        assert isinstance(provider, MockProvider)

    @pytest.mark.asyncio
    async def test_routing_mock_ad_copy_enterprise_stays_mock(self):
        """mock_ad_copy + enterprise → mock（未改动）。"""
        from app.providers.mock_provider import MockProvider

        router = get_provider_router()
        provider = await router.route("mock_ad_copy", "enterprise")
        assert isinstance(provider, MockProvider)

    @pytest.mark.asyncio
    async def test_routing_ocr_still_mock(self):
        """ocr + standard → mock（未改动）。"""
        from app.providers.mock_provider import MockProvider

        router = get_provider_router()
        provider = await router.route("ocr", "standard")
        assert isinstance(provider, MockProvider)

    @pytest.mark.asyncio
    async def test_routing_unknown_feature_falls_back_to_mock(self):
        """未知 feature → mock（回退逻辑未变）。"""
        from app.providers.mock_provider import MockProvider

        router = get_provider_router()
        provider = await router.route("unknown_feature", "standard")
        assert isinstance(provider, MockProvider)

    @pytest.mark.asyncio
    async def test_registry_contains_deepseek(self):
        """Registry 中包含 deepseek provider。"""
        registry = get_provider_registry()
        assert "deepseek" in registry
        assert isinstance(registry.get("deepseek"), DeepSeekProvider)

    @pytest.mark.asyncio
    async def test_registry_still_contains_mock(self):
        """Registry 中仍保留 mock provider。"""
        registry = get_provider_registry()
        assert "mock" in registry
