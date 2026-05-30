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

