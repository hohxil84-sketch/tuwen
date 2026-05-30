---
name: fastapi-backend
description: FastAPI 后端实现 Skill — 云端 API、Auth、Device、Usage、Credit、Provider Log，不能绕开 Provider 层。触发时机：开发云端后台、API 接口、数据库模型、Provider、授权逻辑、扣费系统时。
---

# FastAPI 后端实现 Skill

## 技术栈（固定）

- **框架**: Python FastAPI
- **数据库**: PostgreSQL 或 MySQL（待确认）
- **缓存**: Redis
- **异步任务**: Celery 或 RQ
- **ORM**: SQLAlchemy 或等效

## 云端职责

### ✅ 云端负责

- 登录和 Token 管理（签发、刷新、撤销）
- 设备绑定和校验
- 授权校验（用户状态、设备状态、套餐有效性）
- 套餐和功能权限判定
- AI 算力余额管理和扣除
- Provider 路由和调用
- Provider 调用日志（provider_call_log）
- 使用统计（usage_events）
- 风控日志（risk_logs）
- 成本统计和后台管理

### ❌ 绝不推到客户端

- Provider 路由决策
- AI 算力扣除
- 套餐判断
- 高级 AI 权限判定

## 目录结构

```text
cloud-backend/
  README.md
  app/
    api/          # HTTP 路由（Auth, Device, OCR, Usage, Credit, Provider Log）
    core/         # 配置、鉴权依赖、限流中间件、日志脱敏
    models/       # SQLAlchemy 数据库模型
    schemas/      # Pydantic 请求/响应 DTO
    services/     # 业务逻辑层
    providers/    # AI Provider 层（统一接口）
    workers/      # Celery/RQ 异步任务
    admin/        # 后台管理
  migrations/     # 数据库迁移脚本（必须可回滚）
  tests/          # 测试
```

## Provider 层（不可绕开）

所有 AI 模型调用必须经过 `app/providers/` 层：

```text
app/providers/
  base.py              # 统一接口和返回结构
  openai_provider.py
  deepseek_provider.py
  claude_provider.py
  ocr_provider.py
  image_provider.py
  vector_provider.py
```

### Provider 统一返回结构

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "input_units": 0,
  "output_units": 0,
  "image_units": 0,
  "gpu_seconds": 0,
  "raw_cost": 0.0,
  "estimated_cost": 0.0,
  "currency": "CNY",
  "result": {},
  "raw_usage": {}
}
```

### Provider 调用规则

- 每次调用必须写入 `provider_call_log`
- 必须记录 raw_usage 和 estimated_cost
- 必须支持超时、重试、错误码映射
- 新增 Provider 只能新增文件/注册配置，不能大改业务层

## MVP Sprint-01 模块

只允许开发：
- Auth Service — 登录、Token 刷新、登出
- Device Service — 设备绑定、设备状态
- OCR Service — OCR 任务提交和查询
- Usage Service — 使用事件记录
- Credit Service — 额度查询
- Provider Log Service — 调用日志

## API 规范

- 统一响应结构：`{ success, data, error, request_id }`
- 所有 API 带 request_id
- 错误统一使用错误码（AUTH_REQUIRED、INSUFFICIENT_CREDITS 等）
- API 类型定义同步到 `shared/`

## 授权校验链

所有需登录的 API 必须校验：
1. access token 有效性
2. 用户是否启用
3. 设备是否绑定
4. 设备是否封禁
5. 套餐是否有效
6. 功能是否允许（高级 AI 额外检查额度）

## 安全编码

- 密码只存 hash
- Token 只存 hash 或加密值
- 日志不记录明文密码、Token、API Key
- 所有请求记录 request_id、user_id、device_id、latency_ms
- 禁止 SQL 拼接，必须使用 ORM 参数化查询

## 限流

至少预留：
- 用户级限流
- 设备级限流
- IP 级限流
- 阈值必须配置化，不写死在业务代码中
