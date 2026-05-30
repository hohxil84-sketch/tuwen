"""Pydantic schemas for Auth endpoints."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)
    device_fingerprint: str = Field(..., min_length=1, max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)
    device_fingerprint: str = Field(..., min_length=1, max_length=255)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


# ---------------------------------------------------------------------------
# Response sub-schemas
# ---------------------------------------------------------------------------

class UserInfo(BaseModel):
    id: str
    account: str
    plan_code: str


class DeviceInfo(BaseModel):
    id: str
    status: str
    is_new: bool


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Top-level response data
# ---------------------------------------------------------------------------

class LoginData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
    device: DeviceInfo


class RefreshData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutData(BaseModel):
    message: str = "logged out"
