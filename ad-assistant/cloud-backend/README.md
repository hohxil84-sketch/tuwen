# Cloud Backend — AI 图文广告助手云端后台

## 职责

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

## 技术栈

- **框架**: Python FastAPI
- **数据库**: PostgreSQL 或 MySQL（待确认）
- **缓存**: Redis
- **异步任务**: Celery 或 RQ
- **ORM**: SQLAlchemy 或等效

## 目录结构

```
cloud-backend/
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

## Sprint-01 状态

当前为最小工程骨架。所有模块目录已预留，**尚未实现业务逻辑**。

## 安全红线

- 不下发 API Key 到客户端
- 不由客户端直接调用第三方 AI API
- 不由客户端扣点
- 不由客户端决定套餐和权限
- 所有云端 AI 调用经过 Provider 层并写入 provider_call_log
