# 当前任务：Sprint-01 Task-03 Auth/Device 实现

## 状态

IN_PROGRESS — 等待 Codex Review

## 分支

`feature/sprint-01-auth-device`（基于 `main`）

## 前置任务

- Task-01 项目骨架搭建 ✅ 已完成
- Task-02 Auth/Device 方案设计 ✅ 已完成（方案确认：PostgreSQL, UUID v4, PyJWT + passlib[bcrypt], 3 设备上限, refresh token 30 天轮换, access token 30 分钟内存）

## 本次只开发什么

1. 实现 Auth/Device 模块的 4 张数据库模型（SQLAlchemy 2.0 async）。
2. 实现登录（login）、Token 刷新（refresh）、登出（logout）API。
3. 实现设备绑定查询（bind）和设备列表（list）API。
4. 实现 6 步授权校验链（deps.py）。
5. 实现 Token 轮换 + 重放检测（全部 session 撤销）。
6. 实现反账号枚举（不存在账号与密码错误统一返回 INVALID_CREDENTIALS）。
7. 实现设备上限（3 设备）检查。
8. 输出 4 张 Auth/Device 表的 DDL 草案文件（仅文件，不执行数据库迁移）。
9. 编写 Auth API 和 Device API 的自动化测试（23 个测试用例）。

## 本次不开发什么

- OCR 业务逻辑
- OCR 历史记录
- 使用统计（usage_events）
- Provider 调用日志（provider_call_log）
- 额度系统（credit_accounts / credit_ledger）
- 账号锁定实现（配置已预留，实现推迟到 Task-04+）
- 执行真实数据库迁移（DDL 仅作为文件输出，未执行）
- PPT / Skill 市场 / 插件系统 / AI 工作流 / 自动报价 / 微信机器人 / 云同步
- PS 自动控制 / CDR 自动控制 / 企业私有部署
- 转矢量 / 基础修图 / 高级 AI 修图 / AI 门头效果图
- 支付系统 / 自动更新系统 / 企业后台复杂权限

## 允许修改哪些文件

允许在确认后修改：
- `cloud-backend/app/api/**`
- `cloud-backend/app/core/**`
- `cloud-backend/app/models/**`
- `cloud-backend/app/schemas/**`
- `cloud-backend/app/services/**`
- `cloud-backend/app/main.py`
- `cloud-backend/app/database.py`
- `cloud-backend/migrations/ddl/*.sql`
- `cloud-backend/migrations/migration-plan-draft.md`
- `cloud-backend/tests/**`
- `cloud-backend/pyproject.toml`
- `cloud-backend/docs/dependency-request.md`
- `tasks/current-task.md`

## 禁止修改哪些文件

未经用户再次确认，禁止修改：
- API 契约正式文件（`docs/05-api-contract.md`）
- shared DTO 正式文件
- Tauri 权限配置
- 自动更新配置
- Provider 接口定义
- 支付逻辑
- 与 Sprint-01 Auth/Device 无关的模块

## DDL 文件授权

**允许创建 `migrations/ddl/*.sql` DDL 草案文件**，但明确：
- ✅ 允许：创建 001_users.sql、002_devices.sql、003_auth_sessions.sql、004_risk_logs.sql DDL 草案
- ❌ 禁止：在开发/生产数据库上执行这些 DDL
- ❌ 禁止：运行 Alembic 自动生成迁移
- 📝 说明：DDL 文件按 `migration-plan-draft.md` 中已确认的 PostgreSQL 语法编写，附有 downgrade 注释

## 账号锁定说明

- `MAX_LOGIN_ATTEMPTS=5` 和 `LOGIN_LOCKOUT_SECONDS=900` 已配置在 `config.py`
- **本次不实现**：登录失败计数和锁定逻辑
- 当前行为：登录失败只写入 `risk_logs` 审计日志，不限制重试次数
- 推迟到 Task-04+ 实现（需配合 Redis/内存缓存实现限流）

## 新增依赖申请（✅ 已批准）

Task-03 需要连接 PostgreSQL 数据库、执行 ORM 操作，以下 6 个依赖已经 Codex Review 批准：

### 申请 3：sqlalchemy[asyncio]

| 项目 | 说明 |
|------|------|
| **包名** | `sqlalchemy[asyncio]` |
| **版本** | `>=2.0.0` |
| **用途** | ORM 模型定义、异步查询、session 管理 |
| **许可证** | MIT |
| **体积** | 约 10MB（纯 Python，含 greenlet 二进制依赖） |
| **依赖链** | `greenlet>=1.0`（异步支持所需） |
| **安全风险** | 低。SQLAlchemy 是 Python 生态系统中最广泛使用的 ORM |
| **替代方案** | 1. 手写 SQL（无 ORM 抽象，重复劳动多）2. Peewee（异步支持弱）3. Tortoise ORM（学习成本高） |
| **推荐理由** | FastAPI 官方推荐、SQLAlchemy 2.0 原生异步支持、社区成熟、迁移工具 alembic 原生集成 |

### 申请 4：asyncpg

| 项目 | 说明 |
|------|------|
| **包名** | `asyncpg` |
| **版本** | `>=0.30.0` |
| **用途** | PostgreSQL 异步驱动，SQLAlchemy async 引擎底层 |
| **许可证** | Apache 2.0 |
| **体积** | 约 5MB（含 C 扩展，预编译 wheel 可用） |
| **依赖链** | 无强制依赖 |
| **安全风险** | 低。asyncpg 是 Python PostgreSQL 异步的事实标准驱动 |
| **替代方案** | 1. `psycopg3`（异步支持，但 SQLAlchemy 优先推荐 asyncpg）2. `pg8000`（纯 Python，性能较低） |
| **推荐理由** | SQLAlchemy 2.0 官方推荐 PostgreSQL 异步驱动，性能最佳，生产验证充分 |

### 申请 5：alembic

| 项目 | 说明 |
|------|------|
| **包名** | `alembic` |
| **版本** | `>=1.14.0` |
| **用途** | 数据库迁移管理（自动生成、升级、降级、回滚） |
| **许可证** | MIT |
| **体积** | 约 3MB（纯 Python） |
| **依赖链** | `SQLAlchemy>=1.3.0`, `Mako`（模板引擎） |
| **安全风险** | 低。alembic 是 SQLAlchemy 官方迁移工具 |
| **替代方案** | 1. 手写 SQL 迁移（易出错，无版本管理）2. `yoyo-migrations`（独立迁移工具，不与 SQLAlchemy 集成） |
| **推荐理由** | SQLAlchemy 官方迁移工具，支持自动生成、版本管理、downgrade |

### 申请 6：pydantic-settings

| 项目 | 说明 |
|------|------|
| **包名** | `pydantic-settings` |
| **版本** | `>=2.0.0` |
| **用途** | 从环境变量 / .env 文件加载配置，Pydantic 类型校验 |
| **许可证** | MIT |
| **体积** | 约 1MB（纯 Python） |
| **依赖链** | `pydantic>=2.0.0`（已隐含在 FastAPI 中）, `python-dotenv` |
| **安全风险** | 低。pydantic-settings 是 Pydantic 官方配置管理库 |
| **替代方案** | 1. `os.environ` 手写（无类型校验、无 .env 加载）2. `python-decouple`（不集成 Pydantic） |
| **推荐理由** | Pydantic 官方推荐、类型安全、.env 自动加载、与 FastAPI 生态一致 |

### dev 依赖

| 依赖 | 版本 | 用途 | 许可证 | 风险 |
|------|------|------|--------|------|
| `pytest-asyncio` | `>=0.24.0` | 异步测试 fixture（`pytest_asyncio.fixture`） | Apache 2.0 | 低 |
| `aiosqlite` | `>=0.20.0` | 测试用 SQLite 数据库驱动 | MIT | 低（仅测试） |

### 先前已批准的依赖（Task-02）

| 依赖 | 许可证 | 状态 |
|------|--------|------|
| `PyJWT` | MIT | ✅ 已批准 |
| `passlib[bcrypt]` | BSD | ✅ 已批准 |

### 依赖汇总

| 依赖 | 许可证 | 体积 | 风险 | 状态 |
|------|--------|------|------|------|
| `PyJWT` | MIT | ~0.5MB | 低 | ✅ 已批准 |
| `passlib[bcrypt]` | BSD | ~3MB | 低 | ✅ 已批准 |
| `sqlalchemy[asyncio]` | MIT | ~10MB | 低 | ✅ 已批准 |
| `asyncpg` | Apache 2.0 | ~5MB | 低 | ✅ 已批准 |
| `alembic` | MIT | ~3MB | 低 | ✅ 已批准 |
| `pydantic-settings` | MIT | ~1MB | 低 | ✅ 已批准 |
| `pytest-asyncio` (dev) | Apache 2.0 | ~1MB | 低 | ✅ 已批准 |
| `aiosqlite` (dev) | MIT | ~0.5MB | 低 | ✅ 已批准 |

## 验收标准

Auth API：
- ✅ 用户可以提交账号密码登录 → 返回统一格式 `{success, data, error, request_id}`
- ✅ 云端返回短期 access token + refresh token
- ✅ 设备指纹提交到云端并 hash 存储
- ✅ 云端能判断设备绑定状态
- ✅ 不存在账号与密码错误统一返回 INVALID_CREDENTIALS（401）
- ✅ Token 刷新（rotation）：旧 token 撤销，新 token pair 颁发
- ✅ Token 重放检测：撤销该用户全部 session
- ✅ 3 设备上限：第 4 台设备登录返回 DEVICE_LIMIT_REACHED（403）
- ✅ 6 步授权校验链完整
- ✅ 客户端不保存明文 Token（云端只存 refresh_token hash）

安全：
- ✅ 前端无第三方 AI API Key
- ✅ 前端不直接调用第三方 AI API
- ✅ 客户端不直接扣点
- ✅ 客户端不决定套餐
- ✅ JWT 签名密钥使用默认值时启动拒绝
- ✅ 所有 API 响应遵循统一结构 `{success, data, error, request_id}`

## 测试方式

必须至少提供：
- ✅ 云端 Auth API 测试（14 个测试用例）
- ✅ 设备绑定测试（9 个测试用例）
- ✅ 23/23 通过（in-memory SQLite）

## 是否允许新增依赖

是。6 个依赖已由 Codex 批准（`sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `pytest-asyncio` dev, `aiosqlite` dev）。PyJWT + passlib[bcrypt] 先前已在 Task-02 批准。

## 是否涉及重大变更

否。

原因：Task-03 仅在 cloud-backend 内实现 Auth/Device 业务逻辑，不修改 API 契约文件、Tauri 权限、Provider 接口、数据库结构（DDL 仅草案）。

风险点：
- 数据库模型定义会影响后续迁移
- Token 机制影响安全边界

影响范围：
- `cloud-backend/app/**`
- `cloud-backend/migrations/ddl/*.sql`
- `cloud-backend/tests/**`
- `cloud-backend/pyproject.toml`

回滚方案：
- 通过 Git 分支回滚（当前在 `feature/sprint-01-auth-device`）
- 数据库 DDL 未执行，无回滚需求

是否兼容旧版本：是（无旧版本）。

是否需要数据库迁移：否（DDL 仅草案文件，未在数据库执行）。

## 给 Codex Review 的审查指令

请审查 Task-03 Auth/Device 实现。

重点检查：
1. ✅ 是否按 `docs/auth-device-plan.md` 方案实现
2. ✅ API 响应是否遵循统一结构 `{success, data, error, request_id}`
3. ✅ 反账号枚举是否正确（USER_NOT_FOUND / PASSWORD_WRONG 不得出现在 HTTP 响应）
4. ✅ Token 重放是否触发全量撤销
5. ✅ 设备指纹 hash 是否未在设备列表响应中暴露
6. ✅ 是否存在未批准依赖
7. ✅ JWT 默认密钥是否在启动时被拒绝
8. ✅ DDL 文件是否仅作为草案（未在数据库执行）
9. ✅ 是否存在前端直连第三方 AI API 的代码
10. ✅ 响应/日志中是否泄露 password_hash 或 refresh_token 明文

输出：
- 阻断问题
- 高风险问题
- 中低风险问题
- 验收结论
- 下一步建议
