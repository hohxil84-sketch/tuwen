"""Provider 执行与日志服务 — 调用 Provider、计算成本、扣费、写入 provider_call_log。

不暴露为公共 HTTP API。

Sprint-02 Task-03: MockProvider 专用执行路径。
Sprint-02 Task-09: 新增 ``route_and_execute_provider_call`` 路由层入口。
Sprint-03 Task-03: 真实 credit 扣费（CNY→credits + deduct_credits）。
Sprint-04 Task-01: 预扣检查 + 降级/重试。
"""

import asyncio
import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.providers.base import AsyncProvider, ProviderRequest, ProviderResult
from app.providers.deepseek_provider import DeepSeekProviderError
from app.providers.mock_provider import MockProviderError
from app.providers.registry import get_provider_registry
from app.providers.router import get_provider_router
from app.services.cost_service import (
    calculate_deepseek_cost,
    calculate_mock_cost,
    cny_to_credits,
)
from app.services.credit_service import deduct_credits, get_credit_balance
from app.services.provider_log_service import record_provider_call

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class InsufficientBalanceError(Exception):
    """余额不足以支付本次 Provider 调用（预扣检查拦截）。

    ``error_code`` 为 ``"INSUFFICIENT_BALANCE"``。
    ``message`` 为中文用户提示。
    ``required`` / ``current`` 分别为所需最低积分和当前余额。
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        required: int = 0,
        current: int = 0,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.required = required
        self.current = current
        super().__init__(message)


# ---------------------------------------------------------------------------
# 降级 / 重试配置
# ---------------------------------------------------------------------------

# provider_name → fallback_provider_name（一级降级）
FALLBACK_RULES: dict[str, str] = {
    "deepseek": "mock",
}

# 可重试的错误码（瞬时故障）
_RETRYABLE_ERROR_CODES: frozenset[str] = frozenset(
    {"TIMEOUT", "CONNECTION_ERROR", "API_ERROR"}
)

_MAX_RETRIES: int = 2
_RETRY_BASE_DELAY: float = 1.0  # 秒


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


def _is_retryable(error_code: str | None) -> bool:
    """判断错误码是否为瞬时故障，值得重试。

    可重试：TIMEOUT / CONNECTION_ERROR / API_ERROR (5xx)。
    不可重试：AUTH_ERROR / BAD_REQUEST / RATE_LIMITED 等。
    """
    return error_code in _RETRYABLE_ERROR_CODES if error_code else False


async def _check_balance(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    feature: str,
) -> int:
    """执行两级余额门禁检查。

    第一级：余额 >= ``MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL``（绝对最低）。
    第二级：余额 >= ``FEATURE_MIN_CREDITS[feature]``（feature 最低消耗保护）。

    Returns:
        int: 当前余额。

    Raises:
        InsufficientBalanceError: 余额不足以通过两级门禁。
    """
    balance_info = await get_credit_balance(db=db, user_id=user_id)
    current_balance: int = balance_info["balance"]

    absolute_min: int = settings.MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL
    feature_min: int = settings.FEATURE_MIN_CREDITS.get(feature, absolute_min)
    required: int = max(absolute_min, feature_min)

    if current_balance < required:
        feature_label = f"'{feature}'" if feature else "该功能"
        raise InsufficientBalanceError(
            error_code="INSUFFICIENT_BALANCE",
            message=(
                f"积分余额不足：{feature_label} 需要至少 {required} 积分，"
                f"当前余额 {current_balance} 积分"
            ),
            required=required,
            current=current_balance,
        )

    return current_balance


async def _call_with_retry(
    provider: AsyncProvider,
    request: ProviderRequest,
    *,
    max_retries: int = _MAX_RETRIES,
    base_delay: float = _RETRY_BASE_DELAY,
) -> ProviderResult:
    """调用 Provider，对瞬时故障自动重试（指数退避）。

    仅对 ``_RETRYABLE_ERROR_CODES`` 中的错误码重试。
    不可重试的错误直接抛出，不等待。
    """
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await provider.call(request)
        except (MockProviderError, DeepSeekProviderError) as exc:
            last_error = exc
            if not _is_retryable(getattr(exc, "error_code", None)):
                raise
            if attempt >= max_retries:
                raise
            delay = base_delay * (2**attempt)
            logger.info(
                "Provider call attempt %d/%d failed (%s), retrying in %.1fs ...",
                attempt + 1,
                max_retries + 1,
                exc.error_code,
                delay,
            )
            await asyncio.sleep(delay)
        # 意外异常不重试
        except Exception:
            raise

    # 不应到达此处
    if last_error is not None:
        raise last_error
    raise RuntimeError("_call_with_retry: unexpected exit")


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
    0. **预扣检查**：若 ``user_id`` 不为 None，执行两级余额门禁；
    1. 调用 ``provider.call(request)``（带瞬时故障重试）；
    2. 成功时计算估算成本并扣费；
    3. 写入 ``provider_call_log``（status=success 或 error）；
    4. 返回 ``ProviderResult``。

    错误处理：
    - ``InsufficientBalanceError``：余额不足，记录 error 日志后抛出；
    - ``MockProviderError`` / ``DeepSeekProviderError`` 等可控异常会被捕获
      并以 ``status="error"`` 记录日志后重新抛出；
    - 重试耗尽后抛出的异常同上处理。

    本函数：
    - 不存储 raw prompt、API Key、secret；
    - 余额检查在云端执行，客户端无法绕过；
    - 降级链由 ``route_and_execute_provider_call`` 驱动。
    """
    start_time = time.perf_counter()

    # 生成 request_id（如果调用方未提供）
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    try:
        # ------------------------------------------------------------------
        # 0. 预扣检查（Sprint-04 Task-01）
        # ------------------------------------------------------------------
        if user_id is not None:
            await _check_balance(
                db=db, user_id=user_id, feature=request.feature
            )

        # ------------------------------------------------------------------
        # 1. 调用 Provider（带重试）
        # ------------------------------------------------------------------
        result: ProviderResult = await _call_with_retry(provider, request)

        # ------------------------------------------------------------------
        # 2. 计算估算成本（按 provider 分发）
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
        # 3. 真实 credit 扣费
        # ------------------------------------------------------------------
        credits_charged = 0
        if user_id is not None and estimated_cost > 0:
            credits_to_charge = cny_to_credits(estimated_cost)
            try:
                credits_charged = await deduct_credits(
                    db=db,
                    user_id=user_id,
                    amount=credits_to_charge,
                    source_id=request_id,
                    description=(
                        f"AI call: {request.feature} via "
                        f"{result.provider}/{result.model}"
                    ),
                )
            except Exception:
                # Deduction failed — record an error log and re-raise
                latency_ms = int(
                    (time.perf_counter() - start_time) * 1000
                )
                await record_provider_call(
                    db=db,
                    provider=result.provider,
                    model=result.model,
                    feature=request.feature,
                    status="error",
                    user_id=user_id,
                    device_id=device_id,
                    request_id=request_id,
                    error_code="DEDUCTION_FAILED",
                    prompt_tokens=result.input_units,
                    completion_tokens=result.output_units,
                    total_tokens=result.input_units + result.output_units,
                    estimated_cost=result.estimated_cost,
                    credits_charged=0,
                    latency_ms=latency_ms,
                )
                raise

        result.credits_charged = credits_charged

        # ------------------------------------------------------------------
        # 4. 写入成功日志
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
            credits_charged=credits_charged,
            latency_ms=latency_ms,
        )

        return result

    except InsufficientBalanceError:
        # ------------------------------------------------------------------
        # 余额不足 — 记录 error 日志后抛出（不重试、不降级）
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
            error_code="INSUFFICIENT_BALANCE",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            credits_charged=0,
            latency_ms=latency_ms,
        )

        raise

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

    新增 Sprint-04 Task-01 降级链：
    - 主 Provider 失败时，按 ``FALLBACK_RULES`` 尝试降级 Provider；
    - ``InsufficientBalanceError`` 不触发降级（余额不足换 Provider 也无意义）；
    - 所有 Provider 均失败时抛出最后一个错误。

    This is the recommended high-level entry point for endpoint handlers.
    """
    router = get_provider_router()
    registry = get_provider_registry()
    primary_name = router.resolve_name(feature, plan)

    # 构建降级链：[primary, fallback1]
    provider_names: list[str] = [primary_name]
    fallback_name = FALLBACK_RULES.get(primary_name)
    if fallback_name and fallback_name in registry:
        provider_names.append(fallback_name)

    last_error: Exception | None = None

    for idx, name in enumerate(provider_names):
        is_fallback = idx > 0
        try:
            provider = registry.get(name)
            return await execute_provider_call(
                db=db,
                provider=provider,
                request=request,
                user_id=user_id,
                device_id=device_id,
                request_id=request_id,
            )
        except InsufficientBalanceError:
            # 余额不足 — 不降级，直接上报
            raise
        except (MockProviderError, DeepSeekProviderError) as exc:
            last_error = exc
            if is_fallback:
                logger.warning(
                    "Fallback provider '%s' also failed for feature='%s': %s",
                    name,
                    feature,
                    exc.error_code,
                )
            else:
                logger.info(
                    "Primary provider '%s' failed for feature='%s' "
                    "(%s), trying fallback ...",
                    name,
                    feature,
                    exc.error_code,
                )
            continue
        except Exception as exc:
            last_error = exc
            logger.exception(
                "Unexpected error from provider '%s' for feature='%s'",
                name,
                feature,
            )
            continue

    # 所有 Provider 均失败
    if last_error is not None:
        raise last_error
    raise RuntimeError(
        f"No provider available for feature='{feature}' plan='{plan}'"
    )
