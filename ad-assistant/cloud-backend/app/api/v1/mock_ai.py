"""Mock AI API routes — Sprint-02 Task-04 / Task-08 / Task-09.

受保护 endpoint：POST /api/v1/mock-ai/ad-copy

- 需要 auth + 活跃设备绑定
- Sprint-02 Task-09: 通过 ProviderRouter + route_and_execute_provider_call
  选择 Provider（不再直接实例化 MockProvider）
- 写入 provider_call_log
- 不暴露 raw_usage
- credits_charged 由 provider_service 计算（Sprint-03 Task-03）
- 不写 credit_ledger（由 provider_service 负责）
- Sprint-02 Task-08: 绑定 ``response_model=APIResponse[MockAdCopyData]``，
  使 FastAPI 自动生成正确的 OpenAPI schema 并在运行时校验响应。
"""

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user_with_device,
    verify_feature,
    verify_plan,
)
from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.providers.base import ProviderRequest
from app.schemas.common import APIResponse, success_response
from app.schemas.mock_ai import MockAdCopyData, MockAdCopyRequest
from app.services.provider_service import route_and_execute_provider_call

router = APIRouter(prefix="/api/v1", tags=["Mock AI"])

FEATURE_NAME = "mock_ad_copy"


@router.post(
    "/mock-ai/ad-copy",
    response_model=APIResponse[MockAdCopyData],
    status_code=status.HTTP_200_OK,
)
async def generate_ad_copy(
    body: MockAdCopyRequest,
    request: Request,
    user_and_device: Annotated[tuple[User, Device], Depends(get_current_user_with_device)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """生成 mock 广告文案（mock-only，非真实 AI）。

    需要有效 access token + 活跃设备绑定 + 有效 plan + mock_ad_copy 权限。
    """
    user, device = user_and_device

    # Steps 5-6: plan validity + feature permission
    verify_plan(user)
    verify_feature(user, FEATURE_NAME)

    # 获取或生成 request_id（优先使用 middleware 注入的 X-Request-ID）
    request_id: str = getattr(request.state, "request_id", None) or f"req_{_uuid.uuid4().hex[:12]}"

    # 构建 prompt（用于发送给 Provider，不记录到 provider_call_log / raw_usage）
    selling_points_text = "、".join(body.selling_points)
    prompt = (
        f"为以下产品撰写{body.platform}平台的广告文案，风格为{body.tone}。\n\n"
        f"产品名称：{body.product_name}\n"
        f"卖点：{selling_points_text}"
    )

    # 构建 ProviderRequest —— prompt 文本发送给 Provider 但不记入 raw_usage
    provider_request = ProviderRequest(
        feature=FEATURE_NAME,
        message=prompt,
    )

    # Sprint-02 Task-09: 通过 ProviderRouter 选择 Provider 并执行，
    # 不再直接实例化 MockProvider。
    result = await route_and_execute_provider_call(
        db=db,
        feature=FEATURE_NAME,
        plan=user.plan_code,
        request=provider_request,
        user_id=user.id,
        device_id=device.id,
        request_id=request_id,
    )

    # 构建响应 —— 不暴露 raw_usage
    response_data = MockAdCopyData(
        feature=FEATURE_NAME,
        provider=result.provider,
        model=result.model,
        text=result.result.get("text", "Mock default response."),
        estimated_cost=result.estimated_cost,
        credits_charged=result.credits_charged,
    )

    # Sprint-02 Task-08: 传入 Pydantic model 实例，由 FastAPI 通过
    # response_model=APIResponse[MockAdCopyData] 序列化和校验。
    return success_response(data=response_data, request_id=request_id)
