# 02 系统架构

## 总体架构

```text
Desktop App
  Vue 3 UI
  Pinia State
  Tauri 2 Shell
  SQLite Local DB
  Local FastAPI Service
  Local CLI Tools

Cloud Backend
  FastAPI API
  Auth and Device Binding
  Credit and Cost Service
  Provider Routing
  Provider Call Log
  Usage Statistics
  Admin System
  PostgreSQL or MySQL
  Redis
  Celery or RQ

Official Website
  Next.js
  Tailwind CSS
  Download
  Pricing
  Tutorial
  Register
  SEO

Shared
  OpenAPI
  DTO
  TypeScript Types
  Error Codes
  Constants
  SDK
```

## 请求链路

OCR 最小闭环：
1. 桌面端选择图片。
2. 桌面端检查本地登录态和设备授权缓存。
3. 桌面端向云端校验授权。
4. 云端返回当前用户、套餐、设备状态和可用能力。
5. 桌面端调用本地 FastAPI 服务执行本地 OCR，或调用云端 OCR Provider。
6. 如调用云端 Provider，云端负责 Provider 路由、鉴权、扣费、日志。
7. 桌面端展示 OCR 结果。
8. 桌面端将历史记录写入本地 SQLite。
9. 云端写入使用统计和 Provider 调用日志。

## 分层原则

桌面端只负责：
- UI
- 本地文件选择
- 本地历史记录
- 本地服务调用
- 调用云端业务 API
- 展示云端返回的权限、额度和结果

桌面端不得负责：
- 第三方 AI API Key
- 真实扣点
- 套餐判断
- 高级 AI 权限判定
- Provider 路由策略最终决策

云端负责：
- 登录
- 授权
- 设备绑定
- Token 刷新
- 套餐和权限
- AI 算力扣除
- Provider 调用
- 成本统计
- 风控日志

本地 FastAPI 服务负责：
- 调用本地 OCR、vtracer、ImageMagick 等工具
- 提供受控的本地处理 API
- 不持有云端 Provider API Key
- 不提供远程命令执行能力

## 架构红线

禁止前端直接调用第三方 AI API。
禁止客户端计算并扣除 AI 算力。
禁止客户端决定用户套餐。
禁止本地服务绕过云端授权调用高级能力。

