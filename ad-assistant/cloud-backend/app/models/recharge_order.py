"""RechargeOrder model — 用户充值/购买套餐订单记录."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RechargeOrder(Base):
    """用户充值订单 — 记录每次充值/购买操作的金额和积分。

    当前使用 simulated 支付方式（无真实支付网关）。
    未来接入真实支付后扩展 payment_method 和 status 字段。
    """

    __tablename__ = "recharge_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    plan_code: Mapped[str | None] = mapped_column(String(50))
    amount_cny: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(50), default="simulated", server_default="'simulated'"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="completed", server_default="'completed'"
    )
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
