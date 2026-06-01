"""CreditAccount model — 用户 AI 算力余额账户."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CreditAccount(Base):
    """AI 算力余额账户表 — 每个用户最多一个 active 记录。

    余额和流水只能由云端 service 维护，客户端不可直接写入。
    """

    __tablename__ = "credit_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    plan_code: Mapped[str] = mapped_column(
        String(50), default="standard", server_default="'standard'"
    )
    monthly_grant: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        onupdate=lambda: datetime.now(timezone.utc),
    )
