"""Pydantic schemas for Device endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class BindQueryRequest(BaseModel):
    device_fingerprint: str = Field(..., min_length=1, max_length=255)


class DeviceDetail(BaseModel):
    id: str
    status: str
    device_name: str | None = None
    first_seen_at: datetime | str | None = None
    last_seen_at: datetime | str | None = None


class BindData(BaseModel):
    device_id: str
    status: str
    device_name: str | None = None
    first_seen_at: datetime | str | None = None
    last_seen_at: datetime | str | None = None


class DeviceListData(BaseModel):
    devices: list[DeviceDetail]
