"""Provider 基础接口 — 统一请求/结果结构，所有 Provider 必须遵守。

Sprint-02 Task-03: 从占位骨架升级为带类型的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 统一请求结构
# ---------------------------------------------------------------------------


class ProviderRequest(BaseModel):
    """Provider 调用的最小请求结构。

    不包含 user_id / device_id / request_id —— 这些由 provider_service
    在调用前后注入日志，不与 Provider 本身耦合。
    """

    feature: str = Field(
        default="",
        description="功能标识，例如 ocr、text_gen、image_edit。供 MockProvider 和路由使用。",
    )
    message: str = Field(
        default="",
        description="可选消息/提示文本。不存储原始 prompt。",
    )


# ---------------------------------------------------------------------------
# 统一返回结构
# ---------------------------------------------------------------------------


class ProviderResult(BaseModel):
    """所有 Provider 必须返回的统一结构。

    字段定义与 docs/06-provider-architecture.md 保持一致：
    - 用量字段（input_units / output_units / image_units / gpu_seconds）
      必须非负；
    - raw_cost / estimated_cost 必须非负；
    - raw_usage 不存储原始 prompt 文本、API Key 或用户隐私内容。
    """

    provider: str = Field(..., description="Provider 名称，例如 mock、deepseek")
    model: str = Field(..., description="模型标识，例如 mock-text-v1")
    input_units: int = Field(default=0, ge=0, description="输入单位数（token / 字符）")
    output_units: int = Field(default=0, ge=0, description="输出单位数（token / 字符）")
    image_units: int = Field(default=0, ge=0, description="处理的图片数")
    gpu_seconds: float = Field(default=0.0, ge=0.0, description="GPU 占用秒数")
    raw_cost: float = Field(default=0.0, ge=0.0, description="Provider 原始成本（人民币）")
    estimated_cost: float = Field(default=0.0, ge=0.0, description="后端估算成本（人民币）")
    credits_charged: int = Field(default=0, ge=0, description="实际扣除积分数（Sprint-03 Task-03）")
    currency: str = Field(default="CNY", description="币种")
    result: dict[str, Any] = Field(
        default_factory=dict, description="Provider 返回的业务结果"
    )
    raw_usage: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider 原始用量数据（不包含 prompt、API Key、secret）",
    )


# ---------------------------------------------------------------------------
# 抽象 Provider 接口
# ---------------------------------------------------------------------------


class AsyncProvider(ABC):
    """异步 AI Provider 抽象基类。

    所有具体 Provider 必须实现 ``call(request)``，返回 ``ProviderResult``。
    实现者负责：
    - 将 Provider 原生响应映射为 ``ProviderResult``；
    - 不将 API Key、原始 prompt 或用户隐私写入 ``raw_usage``；
    - 在无网络/超时/鉴权失败等错误场景抛出明确异常。
    """

    @abstractmethod
    async def call(self, request: ProviderRequest) -> ProviderResult:
        """执行一次 AI Provider 调用并返回统一结果。"""
        ...
