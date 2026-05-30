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

`POST /api/v1/usage/events`

用于记录功能使用事件，不允许由客户端提交最终扣费结果。

### Credit

`GET /api/v1/credits/balance`

返回云端计算的可用额度。

### Provider Log

`GET /api/v1/provider-call-logs`

仅后台管理或授权用户可访问。

## 禁止

禁止前端提交：
- 最终套餐
- 最终扣点
- Provider 成本
- 是否允许高级 AI

这些字段只能由云端计算。

