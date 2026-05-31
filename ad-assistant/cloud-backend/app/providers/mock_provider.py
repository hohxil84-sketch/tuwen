"""MockProvider — 确定性、无网络的假 Provider，用于测试和开发。

不导入任何真实 AI SDK，不读取 API Key 或环境变量。
仅用于验证 Provider 执行与日志路径。
"""

from app.providers.base import AsyncProvider, ProviderRequest, ProviderResult


# ---------------------------------------------------------------------------
# 可控错误
# ---------------------------------------------------------------------------


class MockProviderError(Exception):
    """MockProvider 可控失败专用异常。

    仅当 feature 设置为 ``"test-error"`` 时抛出，用于测试 provider_service 的
    错误日志路径。调用方应捕获此异常并以 ``status="error"`` 记录日志。
    """

    def __init__(self, error_code: str = "MOCK_ERROR", message: str = "Controlled mock failure"):
        self.error_code = error_code
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------


class MockProvider(AsyncProvider):
    """确定性 Mock AI Provider。

    - provider 名称：``mock``
    - 模型名称：``mock-text-v1``
    - 不依赖网络、SDK、API Key 或环境变量
    - 同一 feature 每次返回相同结果（确定性）
    - 特殊 feature ``"test-error"`` 会触发 ``MockProviderError``，用于测试错误日志路径
    - ``raw_usage`` 只包含安全元数据，不存储 prompt、key、secret
    """

    PROVIDER_NAME = "mock"
    MODEL_NAME = "mock-text-v1"

    # ------------------------------------------------------------------
    # 确定性模拟数据
    # ------------------------------------------------------------------

    # 不同 feature 的模拟用量配置
    _MOCK_USAGE: dict[str, dict] = {
        "text_gen": {
            "input_units": 150,
            "output_units": 300,
            "image_units": 0,
            "gpu_seconds": 0.05,
            "raw_cost": 0.00012,
            "result": {"text": "Mock generated text — this is a deterministic test output."},
        },
        "ocr": {
            "input_units": 0,
            "output_units": 50,
            "image_units": 1,
            "gpu_seconds": 0.12,
            "raw_cost": 0.0008,
            "result": {"text": "Mock OCR result — deterministic test output."},
        },
        "image_edit": {
            "input_units": 0,
            "output_units": 0,
            "image_units": 1,
            "gpu_seconds": 0.35,
            "raw_cost": 0.002,
            "result": {"url": "mock://edited-image.png"},
        },
    }

    # 未知 feature 的默认配置
    _DEFAULT_USAGE = {
        "input_units": 10,
        "output_units": 20,
        "image_units": 0,
        "gpu_seconds": 0.01,
        "raw_cost": 0.00005,
        "result": {"text": "Mock default response."},
    }

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    async def call(self, request: ProviderRequest) -> ProviderResult:
        """执行一次 mock 调用。

        返回值：
            ProviderResult — 确定性成功结果。

        异常：
            MockProviderError — 当 ``request.feature == "test-error"`` 时，
            用于测试错误日志路径。
        """
        # 可控失败路径：feature 为 "test-error" 时抛出异常
        if request.feature == "test-error":
            raise MockProviderError(
                error_code="MOCK_ERROR",
                message="Controlled mock failure for error-path testing",
            )

        # 查表获取确定性用量
        usage = self._MOCK_USAGE.get(request.feature, self._DEFAULT_USAGE)

        # 构建 raw_usage（仅包含安全元数据，不含 prompt / key / secret）
        raw_usage = {
            "mock_version": "1.0",
            "feature": request.feature,
            "model": self.MODEL_NAME,
            "input_units": usage["input_units"],
            "output_units": usage["output_units"],
            "image_units": usage["image_units"],
            "gpu_seconds": usage["gpu_seconds"],
        }

        return ProviderResult(
            provider=self.PROVIDER_NAME,
            model=self.MODEL_NAME,
            input_units=usage["input_units"],
            output_units=usage["output_units"],
            image_units=usage["image_units"],
            gpu_seconds=usage["gpu_seconds"],
            raw_cost=usage["raw_cost"],
            estimated_cost=0.0,  # 由 cost_service 在外部计算
            currency="CNY",
            result=usage["result"],
            raw_usage=raw_usage,
        )
