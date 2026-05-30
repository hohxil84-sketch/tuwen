# 依赖申请 — Task-02 Auth / Device

> ⚠️ **所有依赖均未安装。** 每项依赖需用户逐项确认后方可添加到 `pyproject.toml`。

---

## 申请 1：PyJWT

| 项目 | 说明 |
|------|------|
| **包名** | `PyJWT` |
| **版本** | `>=2.10.0` |
| **用途** | JWT（JSON Web Token）签发与验证。access_token 需要 HS256 签名、过期校验、载荷解析 |
| **许可证** | MIT |
| **体积** | 约 0.5MB（纯 Python，无二进制依赖） |
| **依赖链** | 无强制依赖（可选 `cryptography` 用于 RS256/ES256，本项目只用 HS256 不需要） |
| **安全风险** | 低。PyJWT 是 JWT 生态最核心的库，被数百万项目使用 |
| **替代方案** | 1. `python-jose[cryptography]`（更重，依赖链更复杂，HS256 场景没有优势）2. 纯标准库 `hmac` + `hashlib` 手写（不推荐，安全敏感代码不宜自造） |
| **推荐理由** | 当前只需 HS256 JWT 签发、过期和 claims 校验，PyJWT 更轻、更直接；`python-jose[cryptography]` 依赖链更重，HS256 场景无必要 |
| **不使用标准库的原因** | JWT 涉及签名算法选择、claims 校验、key 管理，标准库可实现但容易出错，使用成熟库更安全 |

---

## 申请 2：passlib[bcrypt]

| 项目 | 说明 |
|------|------|
| **包名** | `passlib[bcrypt]` |
| **版本** | `>=1.7.4` |
| **用途** | 用户密码 hash 与验证。登录时需对用户输入的密码做 hash 后与 `users.password_hash` 比对 |
| **许可证** | BSD |
| **体积** | 约 3MB（含 bcrypt 依赖） |
| **依赖链** | `bcrypt`（Rust 编译，预编译 wheel 可用） |
| **安全风险** | 低。passlib 是 Python 密码 hash 领域的事实标准库，支持自动升级 hash 算法 |
| **替代方案** | 1. `bcrypt` 直接使用（功能更少）2. `hashlib` + `hashlib.scrypt`（标准库，但缺少自适应升级、hash 格式管理等） |
| **推荐理由** | 支持多种 hash 算法、自动升级 hash、格式管理，减少安全实现失误 |
| **不使用标准库的原因** | `hashlib.scrypt` 可用但缺少自适应方案和 hash 格式迁移能力 |

---

## 不需要的依赖（明确排除 — Task-02 视角，仅保留历史记录）

以下依赖在 Task-02 中**不需要**，Task-01 中已声明的不再重复：

| 依赖 | 不需要的原因 |
|------|-------------|
| `python-multipart` | Task-02 无文件上传，login/refresh/logout 全部 JSON body |
| `fastapi-users` | 过度封装，与项目自定义 auth 链不兼容 |
| `redis` / `aioredis` | Task-02 不需要缓存和限流（后续任务） |
| `httpx` | 已声明在 dev 依赖，非生产依赖 |

> **注意**：`SQLAlchemy`、`alembic`、`asyncpg` 在 Task-02 被标记为"不需要"，但在 Task-03 中因为要实际连接 PostgreSQL 并定义 ORM 模型，已成为必需依赖。见下方 Task-03 申请。

---

## Task-03 新增依赖申请

Task-03 需要连接 PostgreSQL 数据库、执行 ORM 操作、管理配置、编写异步测试。

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
| `pytest-asyncio` | `>=0.24.0` | 异步测试 fixture | Apache 2.0 | 低（仅测试） |
| `aiosqlite` | `>=0.20.0` | 测试用 SQLite 数据库驱动 | MIT | 低（仅测试） |

---

## 依赖汇总（全量）

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

**生产依赖累计：6 个（Task-02: 2 个 + Task-03: 4 个），约 22.5MB。**
**dev 依赖累计：2 个，约 1.5MB。**

---

## 用户确认项

- [x] ~~批准安装 `python-jose[cryptography]`~~ → 改为批准 `PyJWT`
- [x] 批准安装 `passlib[bcrypt]`
- [x] 批准安装 `sqlalchemy[asyncio]`
- [x] 批准安装 `asyncpg`
- [x] 批准安装 `alembic`
- [x] 批准安装 `pydantic-settings`
- [x] 批准安装 `pytest-asyncio`（dev）
- [x] 批准安装 `aiosqlite`（dev）

**2026-05-30 Task-02 确认结果：**
- `PyJWT` **批准** — 纯 Python，仅 HS256 场景更轻（约 0.5MB），替代原方案的 `python-jose[cryptography]`（~2MB 含二进制依赖链）
- `passlib[bcrypt]` **批准**

**2026-05-30 Task-03 确认结果：**
- `sqlalchemy[asyncio]` **批准** — MIT 许可证，ORM + 异步查询，FastAPI 官方推荐
- `asyncpg` **批准** — Apache 2.0 许可证，PostgreSQL 异步驱动，SQLAlchemy 2.0 官方推荐
- `alembic` **批准** — MIT 许可证，数据库迁移管理，SQLAlchemy 官方迁移工具
- `pydantic-settings` **批准** — MIT 许可证，环境变量/配置管理，Pydantic 官方推荐
- `pytest-asyncio` **批准**（dev） — Apache 2.0 许可证，异步测试支持，仅测试环境使用
- `aiosqlite` **批准**（dev） — MIT 许可证，SQLite 测试驱动，仅测试环境使用
