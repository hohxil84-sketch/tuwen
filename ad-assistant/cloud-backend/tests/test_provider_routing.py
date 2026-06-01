"""Sprint-02 Task-09: Provider Routing 聚焦测试。

覆盖：
- ProviderRegistry: register / get / duplicate / missing / list_names / contains
- ProviderRouter: route by (feature, plan) / unknown feature fallback / unknown plan fallback
- Integration: route_and_execute_provider_call 端到端执行
"""

import uuid

import pytest

from app.providers.base import ProviderRequest
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.mock_provider import MockProvider, MockProviderError
from app.providers.registry import (
    ProviderRegistry,
    ProviderRegistryError,
    get_provider_registry,
)
from app.providers.router import (
    DEFAULT_ROUTING_RULES,
    ProviderNotFoundError,
    ProviderRouter,
    get_provider_router,
)
from app.services.provider_service import (
    execute_provider_call,
    route_and_execute_provider_call,
)


# ---------------------------------------------------------------------------
# 1. ProviderRegistry
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    """ProviderRegistry 的注册、查找和错误路径。"""

    def test_register_and_get(self):
        """注册一个 provider 后可通过 get 取回同一实例。"""
        registry = ProviderRegistry()
        mock = MockProvider()
        registry.register("mock", mock)
        assert registry.get("mock") is mock

    def test_register_duplicate_raises(self):
        """重复注册同名 provider 应抛出 ProviderRegistryError。"""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider())
        with pytest.raises(ProviderRegistryError, match="already registered"):
            registry.register("mock", MockProvider())

    def test_get_missing_raises(self):
        """查找未注册的名称应抛出 ProviderRegistryError。"""
        registry = ProviderRegistry()
        with pytest.raises(ProviderRegistryError, match="not registered"):
            registry.get("nonexistent")

    def test_list_names_empty(self):
        """空 registry 返回空列表。"""
        registry = ProviderRegistry()
        assert registry.list_names() == []

    def test_list_names_sorted(self):
        """list_names 返回排序后的名称列表。"""
        registry = ProviderRegistry()
        registry.register("zulu", MockProvider())
        registry.register("alpha", MockProvider())
        assert registry.list_names() == ["alpha", "zulu"]

    def test_contains(self):
        """__contains__ 正确反映注册状态。"""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider())
        assert "mock" in registry
        assert "nonexistent" not in registry

    def test_singleton_returns_same_instance(self):
        """模块级单例 get_provider_registry 多次调用返回同一实例。"""
        r1 = get_provider_registry()
        r2 = get_provider_registry()
        assert r1 is r2

    def test_singleton_has_mock_and_deepseek_pre_registered(self):
        """单例默认预注册了 MockProvider 和 DeepSeekProvider。"""
        registry = get_provider_registry()
        assert "mock" in registry
        assert isinstance(registry.get("mock"), MockProvider)
        assert "deepseek" in registry
        assert isinstance(registry.get("deepseek"), DeepSeekProvider)


# ---------------------------------------------------------------------------
# 2. ProviderRouter
# ---------------------------------------------------------------------------


class TestProviderRouter:
    """ProviderRouter 的路由选择和回退逻辑。"""

    @pytest.fixture
    def registry(self):
        """返回预注册了 mock 和 deepseek 的 registry。"""
        r = ProviderRegistry()
        r.register("mock", MockProvider())
        r.register("deepseek", DeepSeekProvider())
        return r

    @pytest.fixture
    def router(self, registry):
        """返回使用默认路由规则的 router。"""
        return ProviderRouter(registry=registry, rules=DEFAULT_ROUTING_RULES)

    @pytest.mark.anyio
    async def test_route_mock_ad_copy_standard(self, router):
        """mock_ad_copy + standard → deepseek provider (S03-T02)。"""
        provider = await router.route("mock_ad_copy", "standard")
        assert isinstance(provider, DeepSeekProvider)

    @pytest.mark.anyio
    async def test_route_mock_ad_copy_expert(self, router):
        """mock_ad_copy + expert → mock provider。"""
        provider = await router.route("mock_ad_copy", "expert")
        assert isinstance(provider, MockProvider)

    @pytest.mark.anyio
    async def test_route_ocr_enterprise(self, router):
        """ocr + enterprise → mock provider。"""
        provider = await router.route("ocr", "enterprise")
        assert isinstance(provider, MockProvider)

    @pytest.mark.anyio
    async def test_route_unknown_feature_falls_back_to_mock(self, router):
        """未知 feature 应回退到 mock。"""
        provider = await router.route("unknown_feature", "standard")
        assert isinstance(provider, MockProvider)

    @pytest.mark.anyio
    async def test_route_unknown_plan_falls_back_to_mock(self, router):
        """已知 feature + 未知 plan 应回退到 mock。"""
        provider = await router.route("mock_ad_copy", "free_tier")
        assert isinstance(provider, MockProvider)

    @pytest.mark.anyio
    async def test_route_all_combinations_resolve(self, router):
        """所有 (feature, plan) 组合都应解析到已注册的 provider。"""
        features = list(DEFAULT_ROUTING_RULES.keys())
        plans = ["standard", "expert", "enterprise", "free_tier"]
        for feature in features:
            for plan in plans:
                provider = await router.route(feature, plan)
                assert provider is not None, (
                    f"route({feature!r}, {plan!r}) returned None"
                )

    @pytest.mark.anyio
    async def test_route_provider_not_in_registry_raises(self):
        """如果路由解析到的 provider 不在 registry 中，应抛出 ProviderNotFoundError。"""
        registry = ProviderRegistry()
        # 不注册任何 provider — mock 不在 registry 中
        router = ProviderRouter(registry=registry, rules=DEFAULT_ROUTING_RULES)
        with pytest.raises(ProviderNotFoundError, match="not in the registry"):
            await router.route("mock_ad_copy", "standard")

    def test_singleton_returns_same_instance(self):
        """模块级单例 get_provider_router 多次调用返回同一实例。"""
        r1 = get_provider_router()
        r2 = get_provider_router()
        assert r1 is r2


# ---------------------------------------------------------------------------
# 3. Integration: route_and_execute_provider_call
# ---------------------------------------------------------------------------


class TestRouteAndExecute:
    """route_and_execute_provider_call 端到端集成测试。"""

    @pytest.mark.anyio
    async def test_success_returns_provider_result(self, db_session):
        """成功路由 + 执行应返回 ProviderResult（expert plan → mock）。"""
        result = await route_and_execute_provider_call(
            db=db_session,
            feature="mock_ad_copy",
            plan="expert",
            request=ProviderRequest(feature="mock_ad_copy", message=""),
            user_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
        )
        assert result.provider == "mock"
        assert result.model == "mock-text-v1"
        # estimated_cost is computed by cost_service and set on the result
        assert result.estimated_cost >= 0

    @pytest.mark.anyio
    async def test_writes_provider_call_log(self, db_session):
        """应写入 provider_call_log 行。"""
        from app.models.provider_call_log import ProviderCallLog
        from sqlalchemy import func, select

        user_id = uuid.uuid4()
        await route_and_execute_provider_call(
            db=db_session,
            feature="mock_ad_copy",
            plan="expert",
            request=ProviderRequest(feature="mock_ad_copy", message=""),
            user_id=user_id,
            device_id=uuid.uuid4(),
        )
        count = await db_session.scalar(
            select(func.count()).select_from(ProviderCallLog).where(
                ProviderCallLog.user_id == user_id
            )
        )
        assert count == 1

    @pytest.mark.anyio
    async def test_old_execute_provider_call_still_works(self, db_session):
        """原有 execute_provider_call 仍可接受显式 provider 参数。"""
        provider = MockProvider()
        result = await execute_provider_call(
            db=db_session,
            provider=provider,
            request=ProviderRequest(feature="mock_ad_copy", message=""),
            user_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
        )
        assert result.provider == "mock"

    @pytest.mark.anyio
    async def test_route_and_execute_unknown_feature_still_works(self, db_session):
        """未知 feature 通过路由回退到 mock 后应正常执行。"""
        result = await route_and_execute_provider_call(
            db=db_session,
            feature="unknown_feature_xyz",
            plan="standard",
            request=ProviderRequest(feature="unknown_feature_xyz", message=""),
            user_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
        )
        assert result.provider == "mock"
