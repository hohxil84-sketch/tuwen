"""Provider 执行与日志服务 — 调用 Provider、计算成本、写入 provider_call_log。

不执行真实扣费，不写 credit_ledger。
不暴露为公共 HTTP API。

Sprint-02 Task-03: MockProvider 专用执行路径。
Sprint-02 Task-09: 新增 ``route_and_execute_provider_call`` 路由层入口。
"""

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.providers.base import AsyncProvider, ProviderRequest, ProviderResult
from app.providers.deepseek_provider import DeepSeekProviderError
from app.providers.mock_provider import MockProviderError
from app.providers.router import get_provider_router
from app.services.cost_service import calculate_deepseek_cost, calculate_mock_cost
from app.services.provider_log_service import record_provider_call


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------


async def execute_provider_call(
    *,
    db: AsyncSession,
    provider: AsyncProvider,
    request: ProviderRequest,
    user_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    request_id: str | None = None,
) -> ProviderResult:
    """执行一次 Provider 调用并写入日志。

    流程：
    1. 调用 ``provider.call(request)``；
    2. 成功时通过 ``calculate_mock_cost`` 计算估算成本；
    3. 写入 ``provider_call_log``（status=success 或 error）；
    4. 返回 ``ProviderResult``。

    错误处理：
    - ``MockProviderError`` 等可控异常会被捕获并以 ``status="error"`` 记录日志；
    - 异常会被重新抛出，调用方可以决定后续行为。

    本函数：
    - 不存储 raw prompt、API Key、secret；
    - 记录 ``credits_charged=0``（扣费是后续任务）；
    - 不写入 ``credit_ledger``。
    """
    start_time = time.perf_counter()

    # 生成 request_id（如果调用方未提供）
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    try:
        # ------------------------------------------------------------------
        # 调用 Provider
        # ------------------------------------------------------------------
        result: ProviderResult = await provider.call(request)

        # ------------------------------------------------------------------
        # 计算估算成本（按 provider 分发）
        # ------------------------------------------------------------------
        if result.provider == "deepseek":
            estimated_cost = calculate_deepseek_cost(
                input_units=result.input_units,
                output_units=result.output_units,
            )
        else:
            estimated_cost = calculate_mock_cost(
                input_units=result.input_units,
                output_units=result.output_units,
                image_units=result.image_units,
                gpu_seconds=result.gpu_seconds,
            )
        result.estimated_cost = estimated_cost

        # ------------------------------------------------------------------
        # 写入成功日志
        # ------------------------------------------------------------------
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        await record_provider_call(
            db=db,
            provider=result.provider,
            model=result.model,
            feature=request.feature,
            status="success",
            user_id=user_id,
            device_id=device_id,
            request_id=request_id,
            prompt_tokens=result.input_units,
            completion_tokens=result.output_units,
            total_tokens=result.input_units + result.output_units,
            estimated_cost=result.estimated_cost,
            credits_charged=0,  # 扣费在后续任务中实现
            latency_ms=latency_ms,
        )

        return result

    except MockProviderError as exc:
        # ------------------------------------------------------------------
        # MockProvider 可控失败
        # ------------------------------------------------------------------
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        await record_provider_call(
            db=db,
            provider="mock",
            model="mock-text-v1",
            feature=request.feature,
            status="error",
            user_id=user_id,
            device_id=device_id,
            request_id=request_id,
            error_code=exc.error_code,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            credits_charged=0,
            latency_ms=latency_ms,
        )

        raise

    except DeepSeekProviderError as exc:
        # ------------------------------------------------------------------
        # DeepSeekProvider 可控失败
        # ------------------------------------------------------------------
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        await record_provider_call(
            db=db,
            provider="deepseek",
            model=settings.DEEPSEEK_MODEL,
            feature=request.feature,
            status="error",
            user_id=user_id,
            device_id=device_id,
            request_id=request_id,
            error_code=exc.error_code,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            credits_charged=0,
            latency_ms=latency_ms,
        )

        raise

    except Exception:
        # ------------------------------------------------------------------
        # 意外异常：记录 error 日志后重新抛出
        # ------------------------------------------------------------------
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        await record_provider_call(
            db=db,
            provider="unknown",
            model="unknown",
            feature=request.feature,
            status="error",
            user_id=user_id,
            device_id=device_id,
            request_id=request_id,
            error_code="UNKNOWN_PROVIDER_ERROR",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=None,
            credits_charged=0,
            latency_ms=latency_ms,
        )

        raise


# ---------------------------------------------------------------------------
# Sprint-02 Task-09: routing layer
# ---------------------------------------------------------------------------


async def route_and_execute_provider_call(
    *,
    db: AsyncSession,
    feature: str,
    plan: str,
    request: ProviderRequest,
    user_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    request_id: str | None = None,
) -> ProviderResult:
    """Route to the correct provider for *(feature, plan)*, then execute and log.

    This is the recommended high-level entry point for endpoint handlers.
    It delegates provider selection to :class:`ProviderRouter` and then
    calls :func:`execute_provider_call`.

    All routes currently resolve to ``MockProvider`` (``"mock"``).
    """
    router = get_provider_router()
    provider = await router.route(feature, plan)
    return await execute_provider_call(
        db=db,
        provider=provider,
        request=request,
        user_id=user_id,
        device_id=device_id,
        request_id=request_id,
    )
