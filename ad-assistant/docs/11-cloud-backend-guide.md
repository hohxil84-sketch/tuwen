# 11 云端后台指南

## 职责

云端后台负责：
- 登录和 Token
- 设备绑定
- 授权校验
- 套餐和权限
- AI 算力余额
- AI 算力扣除
- Provider 路由
- Provider 调用日志
- 使用统计
- 风控日志
- 后台管理

## 服务分层

建议分层：

```text
app/
  api/        HTTP 路由
  core/       配置、鉴权、限流、日志
  models/     数据库模型
  schemas/    请求响应 DTO
  services/   业务服务
  providers/  AI Provider
  workers/    异步任务
  admin/      后台管理
```

## MVP 模块

Sprint-01 只允许包含：
- Auth Service
- Device Service
- OCR Service
- Usage Service
- Credit Service
- Provider Log Service

## 授权校验

所有需要登录的 API 必须校验：
- access token 是否有效
- 用户是否启用
- 设备是否绑定
- 设备是否封禁
- 套餐是否有效
- 功能是否允许

高级 AI 功能必须额外检查额度和功能权限。

## 限流

MVP 至少预留：
- 用户级限流
- 设备级限流
- IP 级限流

具体限流阈值必须配置化，不得写死在业务逻辑中。

## 日志

必须记录：
- request_id
- user_id
- device_id
- feature
- status
- error_code
- latency_ms

日志不得记录：
- 明文密码
- 明文 Token
- Provider API Key
- 未脱敏身份证、手机号等敏感信息

## 本地开发环境

完整的本地开发启动流程见：

- `docs/25-desktop-mock-e2e-smoke.md` — E2E 运行手册
- `cloud-backend/docs/pg-integration-test-guide.md` — PostgreSQL 集成测试指南
- `cloud-backend/scripts/dev_seed_user.py` — 开发环境种子数据脚本

快速启动（推荐使用 SQLite，避免当前 ORM/DDL DateTime 不匹配问题）：

```bash
cd cloud-backend

# 1. 安装依赖
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -e ".[dev]"

# 2. 创建表并种子测试数据
rm -f dev.db
DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base
import app.models.user, app.models.device, app.models.auth_session
import app.models.risk_log, app.models.usage_event
import app.models.provider_call_log, app.models.credit_account, app.models.credit_ledger
async def init():
    e = create_async_engine('sqlite+aiosqlite:///dev.db')
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await e.dispose()
    print('Tables created')
asyncio.run(init())
"

DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python scripts/dev_seed_user.py

# 3. 启动后端
DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

PostgreSQL 备选路径当前受 ORM/DDL DateTime 类型不匹配影响（DDL 用 `TIMESTAMPTZ`，
模型用 `DateTime` → `TIMESTAMP WITHOUT TIME ZONE`），需先修复方可使用。详见
`docs/25-desktop-mock-e2e-smoke.md` 的已知问题章节。

