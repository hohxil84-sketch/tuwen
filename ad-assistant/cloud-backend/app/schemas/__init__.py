"""Pydantic schemas — request/response DTOs.

All responses follow the unified structure defined in :mod:`app.schemas.common`.
"""
from app.schemas.auth import (
    DeviceInfo,
    LoginData,
    LoginRequest,
    LogoutData,
    LogoutRequest,
    RefreshData,
    RefreshRequest,
    TokenPair,
    UserInfo,
)
from app.schemas.common import APIResponse, ErrorDetail, error_response, success_response
from app.schemas.device import (
    BindData,
    BindQueryRequest,
    DeviceDetail,
    DeviceListData,
)

from app.schemas.provider_log import (
    ProviderCallLogData,
    ProviderCallLogListData,
    ProviderCallLogQueryParams,
)
from app.schemas.usage import (
    UsageEventData,
    UsageEventListData,
    UsageEventQueryParams,
)

__all__ = [
    "APIResponse",
    "ErrorDetail",
    "error_response",
    "success_response",
    "LoginRequest",
    "LoginData",
    "RefreshRequest",
    "RefreshData",
    "LogoutRequest",
    "LogoutData",
    "UserInfo",
    "DeviceInfo",
    "TokenPair",
    "BindQueryRequest",
    "BindData",
    "DeviceDetail",
    "DeviceListData",
    "UsageEventData",
    "UsageEventListData",
    "UsageEventQueryParams",
    "ProviderCallLogData",
    "ProviderCallLogListData",
    "ProviderCallLogQueryParams",
]
