"""开发环境专用：创建本地测试用户及绑定设备。

**警告** 本脚本仅供本地开发使用，严禁在生产环境运行。
        密码、指纹均为固定测试值，不得用于任何线上系统。

用法::

    cd cloud-backend
    python scripts/dev_seed_user.py

环境变量（可选，均有 dev 默认值）::

    DATABASE_URL      默认 postgresql+asyncpg://postgres:postgres@localhost:5432/ad_assistant_dev
    DEV_ACCOUNT       默认 test@example.com
    DEV_PASSWORD      默认 correct-password
    DEV_DEVICE_FINGERPRINT  默认 device-fingerprint-abc

已知限制::

    使用 ORM 模型写库，因此在 PostgreSQL 下依赖 DDL 与模型的 DateTime 列类型
    一致。当前 DDL 使用 TIMESTAMPTZ 而模型使用 TIMESTAMP WITHOUT TIME ZONE，
    会触发 asyncpg 时区不匹配错误。开发时建议使用 SQLite（见运行手册）。
"""

import asyncio
import hashlib
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.models.device import Device
from app.models.user import User

# ---------------------------------------------------------------------------
# 开发默认值（切勿用于生产）
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ad_assistant_dev",
)

DEV_ACCOUNT = os.getenv("DEV_ACCOUNT", "test@example.com")
DEV_PASSWORD = os.getenv("DEV_PASSWORD", "correct-password")
DEV_DEVICE_FINGERPRINT = os.getenv("DEV_DEVICE_FINGERPRINT", "device-fingerprint-abc")
DEV_DEVICE_NAME = os.getenv("DEV_DEVICE_NAME", "Dev Test Machine")


async def seed():
    """使用 ORM 模型写入种子数据，确保 UUID / DateTime 类型与后端一致。"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ----- 检查用户是否已存在 -----
        result = await session.execute(
            select(User).where(User.account == DEV_ACCOUNT)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=uuid.uuid4(),
                account=DEV_ACCOUNT,
                password_hash=hash_password(DEV_PASSWORD),
                plan_code="standard",
                status="active",
            )
            session.add(user)
            await session.flush()
            print(f"[OK] 已创建测试用户: account={DEV_ACCOUNT}")
        else:
            print(f"[SKIP] 测试用户已存在: account={DEV_ACCOUNT}")

        # ----- 检查设备是否已存在 -----
        fp_hash = hashlib.sha256(DEV_DEVICE_FINGERPRINT.encode()).hexdigest()

        result = await session.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_fingerprint_hash == fp_hash,
            )
        )
        device = result.scalar_one_or_none()

        if device is None:
            device = Device(
                id=uuid.uuid4(),
                user_id=user.id,
                device_fingerprint_hash=fp_hash,
                device_name=DEV_DEVICE_NAME,
                status="active",
            )
            session.add(device)
            await session.flush()
            print(f"[OK] 已绑定测试设备: fingerprint={DEV_DEVICE_FINGERPRINT}")
        else:
            print(f"[SKIP] 测试设备已存在: fingerprint={DEV_DEVICE_FINGERPRINT}")

        await session.commit()

    await engine.dispose()

    # ----- 打印开发凭据 -----
    print()
    print("=" * 60)
    print("  本地开发凭据（仅供开发，严禁生产使用）")
    print("=" * 60)
    print(f"  Cloud Backend URL : http://127.0.0.1:8000")
    print(f"  账号 (account)     : {DEV_ACCOUNT}")
    print(f"  密码 (password)    : {DEV_PASSWORD}")
    print(f"  设备指纹 (fingerprint): {DEV_DEVICE_FINGERPRINT}")
    print(f"  设备名称           : {DEV_DEVICE_NAME}")
    print("=" * 60)
    print()
    print("[DONE] 开发种子数据已就绪。")
    print("启动后端前请设置环境变量: JWT_SECRET_KEY=dev-secret-key-not-for-production")


if __name__ == "__main__":
    asyncio.run(seed())
