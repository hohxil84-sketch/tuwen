# 依赖申请 — Task-02 Auth / Device

> ⚠️ **所有依赖均未安装。** 每项依赖需用户逐项确认后方可添加到 `pyproject.toml`。

---

## 申请 1：python-jose（PyJWT 继任者）

| 项目 | 说明 |
|------|------|
| **包名** | `python-jose[cryptography]` |
| **版本** | `>=3.3.0` |
| **用途** | JWT（JSON Web Token）签发与验证。access_token 需要 HS256 签名、过期校验、载荷解析 |
| **许可证** | MIT |
| **体积** | 约 2MB（含 cryptography 依赖） |
| **依赖链** | `cryptography`（Rust 编译，预编译 wheel 可用） |
| **安全风险** | 低。python-jose 是成熟的 JWT 库，被广泛用于 FastAPI 生态 |
| **替代方案** | 1. `PyJWT`（更轻量，功能覆盖）2. 纯标准库 `hmac` + `hashlib` 手写（不推荐，安全敏感代码不宜自造） |
| **推荐理由** | 与 FastAPI 生态一致，文档丰富，社区活跃，安全性经审计 |
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

## 不需要的依赖（明确排除）

以下依赖在 Task-02 中**不需要**，Task-01 中已声明的不再重复：

| 依赖 | 不需要的原因 |
|------|-------------|
| `python-multipart` | Task-02 无文件上传，login/refresh/logout 全部 JSON body |
| `fastapi-users` | 过度封装，与项目自定义 auth 链不兼容 |
| `SQLAlchemy` | Task-02 不执行迁移，DDL 手写 SQL |
| `alembic` | Task-02 不执行迁移 |
| `asyncpg` / `mysql-connector` | Task-02 不实际连接数据库 |
| `redis` / `aioredis` | Task-02 不需要缓存和限流（后续任务） |
| `httpx` | 已声明在 dev 依赖，非生产依赖 |

---

## 依赖汇总

| 依赖 | 许可证 | 体积 | 风险 | 是否需要确认 |
|------|--------|------|------|-------------|
| `python-jose[cryptography]` | MIT | ~2MB | 低 | ✅ 待确认 |
| `passlib[bcrypt]` | BSD | ~3MB | 低 | ✅ 待确认 |

**总计新增：2 个依赖，约 5MB。**

---

## 用户确认项

- [ ] 批准安装 `python-jose[cryptography]`
- [ ] 批准安装 `passlib[bcrypt]`
- [ ] 或者：指定替代方案
