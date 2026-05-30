# Auth / Device 最小闭环方案

> Sprint-01 Task-02 主方案文档。本文只描述方案，不包含任何实现代码。

---

## 一、整体流程

### 1.1 登录流程

```
Client                          Cloud Backend
  │                                  │
  │  POST /api/v1/auth/login         │
  │  { account, password,            │
  │    device_fingerprint }          │
  │ ─────────────────────────────>   │
  │                                  │ 1. 查询 users 表验证账号
  │                                  │ 2. 校验 password_hash
  │                                  │ 3. 查询/创建设备记录
  │                                  │ 4. 检查设备状态（禁用/正常）
  │                                  │ 5. 签发 access_token (JWT, 30min)
  │                                  │ 6. 生成 refresh_token (随机字符串)
  │                                  │ 7. refresh_token 仅存 hash 到 auth_sessions
  │                                  │ 8. 明文 refresh_token 返回客户端（仅此一次）
  │  { access_token, refresh_token,  │
  │    expires_in, user, device }    │
  │ <─────────────────────────────   │
  │                                  │
  │ 客户端：                          │
  │ - access_token 存内存             │
  │ - refresh_token 存系统安全存储     │
  │ - 不存明文到 SQLite / localStorage │
```

### 1.2 Token 刷新流程

```
Client                          Cloud Backend
  │                                  │
  │  POST /api/v1/auth/refresh       │
  │  { refresh_token,                │
  │    device_fingerprint }          │
  │ ─────────────────────────────>   │
  │                                  │ 1. hash refresh_token
  │                                  │ 2. 查询 auth_sessions 匹配
  │                                  │ 3. 检查未过期、未撤销
  │                                  │ 4. 检查设备未被禁用
  │                                  │ 5. 撤销旧 session
  │                                  │ 6. 签发新 token pair（rotation）
  │  { access_token, refresh_token,  │
  │    expires_in }                  │
  │ <─────────────────────────────   │
```

### 1.3 登出流程

```
Client                          Cloud Backend
  │                                  │
  │  POST /api/v1/auth/logout        │
  │  { refresh_token }  (可选)       │
  │ ─────────────────────────────>   │
  │                                  │ 1. 撤销 auth_sessions 中该 token
  │                                  │ 2. 客户端清理本地存储
  │  { success: true }               │
  │ <─────────────────────────────   │
```

---

## 二、授权校验链（6 步）

每次需要授权的请求（OCR、设备查询等）必须经过以下校验链：

```
请求到达
  │
  ├─ 1. 提取并验证 access_token（JWT 签名 + 过期）
  │    失败 → 401 AUTH_REQUIRED
  │
  ├─ 2. 查询用户状态（users.status）
  │    非 active → 403 USER_DISABLED
  │
  ├─ 3. 校验设备绑定
  │    device_id 不属于 user → 403 DEVICE_NOT_BOUND
  │
  ├─ 4. 校验设备状态（devices.status）
  │    非 active → 403 DEVICE_BANNED
  │
  ├─ 5. 校验套餐有效
  │    plan_code 无效 → 403 PLAN_INVALID
  │
  └─ 6. 校验功能权限
       feature 不在允许列表 → 403 FEATURE_NOT_ALLOWED
```

---

## 三、Token 设计

### 3.1 access_token

| 属性 | 值 |
|------|-----|
| 格式 | JWT（HS256 签名） |
| 有效期 | 30 分钟（可配置） |
| 载荷 | `{ sub: user_id, device_id, plan, iat, exp, jti }` |
| 存储 | 客户端内存，不落盘 |
| 传输 | Authorization: Bearer \<token\> |

### 3.2 refresh_token

| 属性 | 值 |
|------|-----|
| 格式 | 随机字符串（secrets.token_urlsafe(32)） |
| 有效期 | 30 天（可配置） |
| 存储 | 云端仅存 hash（SHA-256），客户端存系统安全存储 |
| 传输 | HTTPS Body，不在 URL 中 |
| 轮换 | 每次 refresh 颁发新 token，撤销旧 token |

### 3.3 安全红线

- ❌ 禁止在 URL query string 中传递 token
- ❌ 禁止在日志中输出 token 明文
- ❌ 禁止在 SQLite / localStorage / sessionStorage 中存明文 token
- ❌ 禁止在 API 响应中返回 password_hash 或 password
- ✅ refresh_token 云端只存 hash
- ✅ 登录成功仅返回一次明文 refresh_token
- ✅ 检测到 token 重用立即撤销该用户所有 session（防重放）

---

## 四、设备绑定

### 4.1 设备指纹

客户端在登录时提交 `device_fingerprint`，由客户端基于以下信息生成 hash：

- 操作系统版本
- 硬件标识（不涉及 MAC 地址等隐私）
- 应用安装 ID（首次安装时生成）

云端不接触原始设备信息，只存储 `device_fingerprint_hash`。

### 4.2 绑定规则

| 场景 | 行为 |
|------|------|
| 新设备首次登录 | 自动创建 devices 记录，status=active |
| 已有设备登录 | 更新 last_seen_at |
| 设备数超限（>N） | 拒绝登录，返回 DEVICE_LIMIT_REACHED |
| 设备被管理员禁用 | 拒绝该设备的请求，返回 DEVICE_BANNED |

### 4.3 设备状态

| 状态 | 含义 |
|------|------|
| `active` | 正常使用 |
| `banned` | 管理员封禁 |
| `unbound` | 用户主动解绑 |

---

## 五、错误码草案

| 错误码 | HTTP | 含义 |
|--------|------|------|
| `AUTH_REQUIRED` | 401 | 缺少或无效 access_token |
| `TOKEN_EXPIRED` | 401 | access_token 过期，需 refresh |
| `REFRESH_INVALID` | 401 | refresh_token 无效或已撤销 |
| `REFRESH_EXPIRED` | 401 | refresh_token 过期，需重新登录 |
| `TOKEN_REUSE` | 401 | 检测到 refresh_token 重用，全部 session 撤销 |
| `USER_NOT_FOUND` | 401 | 账号不存在 |
| `PASSWORD_WRONG` | 401 | 密码错误 |
| `USER_DISABLED` | 403 | 用户已禁用 |
| `DEVICE_NOT_BOUND` | 403 | 设备未绑定到当前用户 |
| `DEVICE_BANNED` | 403 | 设备已被封禁 |
| `DEVICE_LIMIT_REACHED` | 403 | 设备数量超限 |
| `PLAN_INVALID` | 403 | 套餐无效或已过期 |
| `FEATURE_NOT_ALLOWED` | 403 | 当前套餐不支持该功能 |

---

## 六、Task-02 所需数据库表

Task-02 实现 Auth / Device 最小闭环需要以下 4 张表：

| 表 | 用途 | 优先级 |
|----|------|--------|
| `users` | 用户账号与密码 hash | 必须 |
| `devices` | 设备绑定与状态 | 必须 |
| `auth_sessions` | Token 会话管理 | 必须 |
| `risk_logs` | 风控审计日志 | 必须 |

DDL 详见 [migration-plan-draft.md](../migrations/migration-plan-draft.md) 中相应部分。

Task-02 **不需要**以下表（属于后续任务）：
- `credit_accounts` / `credit_ledger` → Task-03+
- `usage_events` → Task-03+
- `provider_call_log` → Task-04+

---

## 七、测试计划

### 7.1 功能测试

| 测试场景 | 预期结果 |
|----------|----------|
| 正确账号密码登录 | 200，返回 token pair + user info |
| 错误密码登录 | 401 PASSWORD_WRONG |
| 不存在账号登录 | 401 USER_NOT_FOUND |
| 有效 refresh_token 刷新 | 200，返回新 token pair，旧 token 撤销 |
| 过期 refresh_token 刷新 | 401 REFRESH_EXPIRED |
| 已撤销 refresh_token 刷新 | 401 REFRESH_INVALID |
| refresh_token 重用（重放） | 401 TOKEN_REUSE，该用户所有 session 撤销 |
| 有效 access_token 访问受保护资源 | 通过校验链 |
| 过期 access_token 访问受保护资源 | 401 TOKEN_EXPIRED |
| 新设备首次绑定 | 自动创建，状态 active |
| 被禁用设备请求 | 403 DEVICE_BANNED |

### 7.2 安全测试

| 测试场景 | 预期结果 |
|----------|----------|
| 日志中不含 password 明文 | 所有日志行检查通过 |
| 日志中不含 refresh_token 明文 | 所有日志行检查通过 |
| 响应中不含 password_hash | 所有响应体检查通过 |
| 客户端 SQLite 不含明文 token | SQLite 检查通过 |
| 无 API Key 泄露 | 源码 + 配置检查通过 |

### 7.3 安全红线测试（Codex Review）

| 测试场景 | 预期结果 |
|----------|----------|
| 前端无第三方 AI API Key | 源码扫描通过 |
| 前端不直接调用第三方 AI API | 源码扫描通过 |
| 客户端不直接扣点 | 源码扫描通过 |
| 客户端不决定套餐 | 源码扫描通过 |
| 不保存明文 Token | 存储检查通过 |
| 所有云端 AI 调用经过 Provider 层 | 架构检查通过 |

---

## 八、失败场景与降级

| 场景 | 行为 |
|------|------|
| 数据库不可用 | 返回 503，不泄露连接信息 |
| JWT 签名密钥未配置 | 启动时检查，缺失则拒绝启动 |
| 设备指纹为空 | 拒绝登录，返回 INVALID_DEVICE |
| 并发刷新同一 refresh_token | 第一个成功，后续检测到重用 → 全部撤销 |

---

## 九、依赖分析

详见 [dependency-request.md](dependency-request.md)。

Task-02 可能需要 2 个新依赖：

1. **python-jose** — JWT 签发与验证
2. **passlib[bcrypt]** — 密码 hash 与验证

均未安装，需等待用户确认。
