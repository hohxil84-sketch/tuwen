# API 草案 — Auth / Device

> ⚠️ **草案文档。** 本文不是正式 API 契约，不修改 `shared/openapi/`。最终 API 以 OpenAPI 文件为准。

---

## 通用约定

- Base URL：`https://api.example.com/api/v1`
- Content-Type：`application/json`
- 认证方式：`Authorization: Bearer <access_token>`
- 统一响应结构见 [05-api-contract.md](../../docs/05-api-contract.md)

---

## 1. POST /api/v1/auth/login

### 用途

用户登录，返回 token pair。

### 请求

```json
{
  "account": "user@example.com",
  "password": "secure_password",
  "device_fingerprint": "sha256_hash_of_device_info"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| account | string | 是 | 用户账号（邮箱或手机号） |
| password | string | 是 | 明文密码（仅传输时，服务端不记录） |
| device_fingerprint | string | 是 | 客户端生成的设备指纹 hash |

### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "account": "user@example.com",
      "plan_code": "standard"
    },
    "device": {
      "id": "uuid",
      "status": "active",
      "is_new": false
    }
  },
  "error": null,
  "request_id": "req_xxx"
}
```

### 错误响应

| 错误码 | HTTP | 说明 |
|--------|------|------|
| `USER_NOT_FOUND` | 401 | 账号不存在 |
| `PASSWORD_WRONG` | 401 | 密码错误 |
| `USER_DISABLED` | 403 | 用户已被禁用 |
| `DEVICE_LIMIT_REACHED` | 403 | 设备绑定数超限 |
| `INVALID_DEVICE` | 400 | 设备指纹格式无效 |
| `VALIDATION_ERROR` | 422 | 请求体格式错误 |

### 安全注意事项

- 登录成功仅返回一次明文 refresh_token
- password 不写入任何日志
- 登录失败写入 risk_logs（event_type=LOGIN_FAILED）
- 同一账号连续失败 5 次后临时锁定 15 分钟

---

## 2. POST /api/v1/auth/refresh

### 用途

使用 refresh_token 换取新的 token pair。

### 请求

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "device_fingerprint": "sha256_hash_of_device_info"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 上次登录或刷新获得的 refresh_token |
| device_fingerprint | string | 是 | 当前设备指纹，用于校验设备未被替换 |

### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "bmV3IHJlZnJlc2ggdG9r...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "error": null,
  "request_id": "req_xxx"
}
```

### 错误响应

| 错误码 | HTTP | 说明 |
|--------|------|------|
| `REFRESH_INVALID` | 401 | refresh_token 无效或已撤销 |
| `REFRESH_EXPIRED` | 401 | refresh_token 已过期 |
| `TOKEN_REUSE` | 401 | 检测到 refresh_token 重用，该用户所有 session 已撤销 |
| `DEVICE_BANNED` | 403 | 设备已被封禁 |

### Token 轮换规则

- 每次 refresh 成功 → 撤销旧 refresh_token → 签发新 refresh_token
- 如果发现已撤销的 refresh_token 再次被使用 → 视为重放攻击 → 撤销该用户所有 session

---

## 3. POST /api/v1/auth/logout

### 用途

登出，撤销 refresh_token。

### 请求

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 否 | 要撤销的 refresh_token。不提供则仅返回成功，客户端自行清理 |

### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "message": "logged out"
  },
  "error": null,
  "request_id": "req_xxx"
}
```

### 行为

- 如果提供了 refresh_token：撤销对应 auth_sessions 记录
- 客户端必须清除本地存储的 access_token 和 refresh_token
- logout 不要求 access_token 有效（避免因 token 过期无法登出）

---

## 4. POST /api/v1/devices/bind

### 用途

查询当前设备绑定状态（客户端可主动了解设备绑定情况）。

### 请求

```json
{
  "device_fingerprint": "sha256_hash_of_device_info"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_fingerprint | string | 是 | 设备指纹 hash |

### 认证

需要 Authorization header（access_token）。

### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "device_id": "uuid",
    "status": "active",
    "device_name": "Windows 10 Desktop",
    "first_seen_at": "2026-05-30T10:00:00Z",
    "last_seen_at": "2026-05-30T17:00:00Z"
  },
  "error": null,
  "request_id": "req_xxx"
}
```

### 注意

- 设备在首次登录时自动绑定，不需要额外调用本接口创建绑定
- 本接口仅用于查询当前设备状态
- 如设备指纹不匹配任何已绑定设备，返回 403 DEVICE_NOT_BOUND

---

## 5. GET /api/v1/devices/current

### 用途

获取当前用户所有已绑定设备列表。

### 请求

无请求体。

### 认证

需要 Authorization header（access_token）。

### 成功响应 (200)

```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "id": "uuid-1",
        "device_name": "Windows 10 Desktop",
        "status": "active",
        "first_seen_at": "2026-05-01T08:00:00Z",
        "last_seen_at": "2026-05-30T17:00:00Z"
      },
      {
        "id": "uuid-2",
        "device_name": "MacBook Pro",
        "status": "active",
        "first_seen_at": "2026-05-15T09:00:00Z",
        "last_seen_at": "2026-05-29T12:00:00Z"
      }
    ]
  },
  "error": null,
  "request_id": "req_xxx"
}
```

### 注意

- 不返回设备指纹 hash
- 不返回敏感设备信息
- 只返回当前用户的设备

---

## 补充说明

1. **非正式契约**：本文档是草案，最终 API 定义以 `shared/openapi/` 中的 OpenAPI 文件为准
2. **不修改正式文件**：Task-02 不会修改 `shared/openapi/` 中的任何文件
3. **无实现代码**：本任务只输出方案，不编写路由处理函数、模型、服务层代码
4. **字段可调整**：请求/响应字段在实现阶段可根据实际需要微调
5. **版本化**：所有端点以 `/api/v1/` 为前缀
