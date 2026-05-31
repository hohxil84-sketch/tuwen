"""Mock AI API schemas — Sprint-02 Task-04.

请求/响应模式，用于 POST /api/v1/mock-ai/ad-copy。
客户端不可提交 provider、model、cost、credits、user_id、device_id 或 request_id。
"""

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 请求
# ---------------------------------------------------------------------------

SELLING_POINTS_MAX_ITEMS = 5
SELLING_POINT_MAX_LENGTH = 200


class MockAdCopyRequest(BaseModel):
    """mock 广告文案生成请求。

    所有字段都由后端校验边界；客户端不可提交 provider/model/cost/credits。
    """

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="产品/服务名称",
    )
    selling_points: list[str] = Field(
        default_factory=list,
        max_length=SELLING_POINTS_MAX_ITEMS,
        description="卖点列表（最多 5 条）",
    )
    platform: str = Field(
        default="douyin",
        min_length=1,
        max_length=50,
        description="投放平台，例如 douyin、xiaohongshu",
    )
    tone: str = Field(
        default="direct",
        min_length=1,
        max_length=50,
        description="文案风格，例如 direct、soft、storytelling",
    )

    @field_validator("selling_points")
    @classmethod
    def _validate_selling_point_items(cls, v: list[str]) -> list[str]:
        """校验每条卖点长度不超过 SELLING_POINT_MAX_LENGTH."""
        for i, item in enumerate(v):
            if len(item) > SELLING_POINT_MAX_LENGTH:
                raise ValueError(
                    f"selling_points[{i}] exceeds {SELLING_POINT_MAX_LENGTH} characters"
                )
        return v


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


class MockAdCopyData(BaseModel):
    """mock 广告文案生成响应 data。

    ``raw_usage`` 不返回给客户端。
    """

    feature: str = Field(..., description="功能标识")
    provider: str = Field(..., description="Provider 名称")
    model: str = Field(..., description="模型标识")
    text: str = Field(..., description="生成的 mock 广告文案")
    estimated_cost: float = Field(..., description="后端估算成本（人民币）")
    credits_charged: int = Field(..., description="本次消耗点数（当前固定为 0）")
