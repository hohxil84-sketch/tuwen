"""Plan model — 会员套餐/方案定义表."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Plan(Base):
    """可用套餐定义 — 存储各档套餐的元数据和定价。

    由 seed data 初始化，管理员可通过后台管理（未来功能）。
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_cny: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_credits: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    features_json: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="'active'"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
