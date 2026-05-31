# 05 API 契约

## 原则

API 契约必须稳定、可版本化、可生成类型。

所有前后端交互以 `shared/openapi/` 为准。

修改 API 契约属于重大变更，必须先确认。

## API 分组

MVP API 分组：
- Auth API
- Device API
- OCR API
- Usage API
- Credit API
- Provider Log API

## 统一响应结构

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "req_xxx"
}
```

错误响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required",
    "details": {}
  },
  "request_id": "req_xxx"
}
```

## MVP API 草案

### Auth

`POST /api/v1/auth/login`

请求：
```json
{
  "account": "user@example.com",
  "password": "password",
  "device_fingerprint": "device_hash"
}
```

响应：
```json
{
  "access_token": "short_lived_token",
  "refresh_token": "refresh_token",
  "expires_in": 1800,
  "user": {
    "id": "user_id",
    "plan": "standard"
  }
}
```

`POST /api/v1/auth/refresh`

`POST /api/v1/auth/logout`

### Device

`POST /api/v1/devices/bind`

`GET /api/v1/devices/current`

### OCR

`POST /api/v1/ocr/tasks`

云端 OCR 请求必须由云端检查授权和额度。

响应必须包含：
- `task_id`
- `status`
- `text_blocks`
- `provider`
- `estimated_cost`
- `credits_charged`

### Usage

`GET /api/v1/usage/events`

Sprint-01 当前实现用于查询当前登录用户自己的使用事件。

要求：
- 必须鉴权。
- 普通用户只能查询自己的 `usage_events`。
- 支持 `limit`、`offset`、`feature` 查询参数。
- 按 `created_at` 倒序返回。
- 返回统一结构 `{success, data, error, request_id}`。

当前返回 `data` 结构：
```json
{
  "items": [
    {
      "id": "event_id",
      "user_id": "user_id",
      "device_id": "device_id",
      "event_type": "OCR_LOCAL",
      "feature": "ocr",
      "request_id": "req_xxx",
      "metadata_json": {},
      "created_at": "2026-05-30T00:00:00+00:00"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

说明：
- 使用事件写入由后端 service 内部调用完成。
- 当前不暴露客户端直接写入使用事件的 POST API。
- 不允许由客户端提交最终扣费结果。

### Credit

`GET /api/v1/credits/balance`

返回云端计算的可用额度。

### Provider Log

`GET /api/v1/provider-call-logs`

Sprint-01 当前实现允许普通用户查询自己的 Provider 调用日志；后台管理查询另行任务实现。

要求：
- 必须鉴权。
- 普通用户只能查询自己的 `provider_call_log`。
- 支持 `limit`、`offset`、`feature`、`status` 查询参数。
- 按 `created_at` 倒序返回。
- 返回统一结构 `{success, data, error, request_id}`。
- 不返回 prompt 原文、图片原文、API Key、Token、完整隐私内容。

当前返回 `data` 结构：
```json
{
  "items": [
    {
      "id": "log_id",
      "request_id": "req_xxx",
      "user_id": "user_id",
      "device_id": "device_id",
      "provider": "deepseek",
      "model": "deepseek-chat",
      "feature": "ocr",
      "status": "success",
      "error_code": null,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0,
      "estimated_cost": 0,
      "credits_charged": 0,
      "latency_ms": 100,
      "created_at": "2026-05-30T00:00:00+00:00"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## 禁止

禁止前端提交：
- 最终套餐
- 最终扣点
- Provider 成本
- 是否允许高级 AI

这些字段只能由云端计算。
