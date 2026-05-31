# 当前任务：Sprint-01 Task-05 使用统计基础表 + provider_call_log 表

## 状态

`MVP_REQUIRED` — 由 CC 实现，Codex Review

## 分支

`feature/sprint-01-usage-provider-log`（基于 `main`，commit 599e2b0）

## 前置任务

- Task-01 项目骨架搭建 ✅ 已完成
- Task-02 Auth/Device 方案设计 ✅ 已完成
- Task-03 Auth/Device 实现 ✅ 已完成（已合并到 main）
- Task-04 OCR 最小闭环 ✅ 已完成（已合并到 main）

## 背景

Sprint-01 需要完成基础数据闭环。Task-03 实现了 Auth/Device 鉴权，Task-04 实现了本地 OCR。Task-05 建立"使用统计"和"Provider 调用审计"两张基础表，为后续云端 Provider 调用、扣费、风控打下地基。

本轮只建表和最小写入/查询能力，不接入真实 AI Provider，不做真实扣费，不做复杂报表。

## 本次只开发什么

### 1. usage_events 基础表

新建 `usage_events` 表，记录功能使用事件。

最低字段：
- `id` UUID PRIMARY KEY
- `user_id` UUID → users(id)，可为空
- `device_id` UUID → devices(id)，可为空
- `event_type` VARCHAR NOT NULL（如 `OCR_LOCAL`、`FEATURE_CLICK`）
- `feature` VARCHAR NOT NULL（如 `ocr`、`vectorize`）
- `request_id` VARCHAR（关联 API 请求 ID，可为空）
- `metadata_json` JSONB（扩展元数据，可为空）
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

安全约束：
- `metadata_json` 不允许保存图片、OCR 全文、Token、API Key、用户敏感原文
- 为 `user_id`、`device_id`、`feature`、`created_at` 建必要索引

### 2. provider_call_log 基础表

新建 `provider_call_log` 表，记录所有 Provider 调用和成本。

最低字段：
- `id` UUID PRIMARY KEY
- `request_id` VARCHAR（关联 API 请求 ID）
- `user_id` UUID → users(id)，可为空
- `device_id` UUID → devices(id)，可为空
- `provider` VARCHAR NOT NULL（如 `deepseek`、`openai`、`paddleocr`）
- `model` VARCHAR NOT NULL（如 `deepseek-chat`、`gpt-4o`）
- `feature` VARCHAR NOT NULL（如 `ocr`、`vectorize`）
- `status` VARCHAR NOT NULL（`success` / `error`）
- `error_code` VARCHAR（失败时的错误码，可为空）
- `prompt_tokens` INTEGER DEFAULT 0
- `completion_tokens` INTEGER DEFAULT 0
- `total_tokens` INTEGER DEFAULT 0
- `estimated_cost` NUMERIC(12,8)（云端估算成本，可为空）
- `credits_charged` INTEGER DEFAULT 0（扣费点数，可为空）
- `latency_ms` INTEGER（调用耗时，可为空）
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

安全约束：
- `credits_charged` 可以为 0 或 nullable，但字段要预留
- `estimated_cost` 只能由后端计算或记录，不能来自前端
- 失败调用也要能记录 status/error_code
- 不记录 prompt 原文、图片原文、API Key、完整用户隐私内容
- 为 `user_id`、`device_id`、`provider`、`feature`、`status`、`created_at` 建必要索引

### 3. 后端写入/查询服务

- `record_usage_event()` — 记录一条使用事件（由其他模块调用）
- `record_provider_call()` — 记录一条 Provider 调用（由 Provider 层调用）
- `list_usage_events()` — 查询用户自己的使用事件（分页、可按 feature 筛选）
- `list_provider_call_logs()` — 查询用户自己的调用日志（分页、可按 feature/status 筛选）

### 4. 最小查询 API

- `GET /api/v1/usage/events?limit=50&offset=0&feature=ocr`
  - 必须鉴权
  - 普通用户只能查自己的数据
  - 返回统一结构 `{success, data, error, request_id}`

- `GET /api/v1/provider-call-logs?limit=50&offset=0&feature=ocr&status=success`
  - 必须鉴权
  - 普通用户只能查自己的数据
  - 返回统一结构 `{success, data, error, request_id}`

### 5. 自动化测试

- migration 测试或表结构测试（确认表存在、列正确）
- usage_events 写入测试
- provider_call_log 写入成功记录测试
- provider_call_log 失败记录测试
- 查询接口鉴权测试（无 token → 401）
- 查询接口不能越权访问其他用户数据测试
- 敏感字段不落库测试（metadata_json 不含 Token/API Key/图片原文/OCR 全文）

## 本次不开发什么

- ❌ 不修改 OCR 本地服务
- ❌ 不修改 PaddleOCR
- ❌ 不调用真实 OpenAI/Claude/DeepSeek/图片 Provider
- ❌ 不把 API Key 发给前端或桌面端
- ❌ 不实现会员、套餐、支付、充值
- ❌ 不实现 credit_ledger 扣费逻辑
- ❌ 不实现 complex 后台报表
- ❌ 不改 Auth/Device 核心逻辑（仅读取 user_id/device_id）
- ❌ 不改 Tauri 权限
- ❌ 不引入大依赖
- ❌ 不实现 POST 写入 API（记录由内部服务调用，不暴露给客户端直接写入）
- ❌ 不做管理员系统
- ❌ 不做真实扣费
- ❌ 不做前端页面

## 允许修改哪些文件

允许在确认后修改：

cloud-backend 模型：
- `cloud-backend/app/models/usage_event.py`（新文件）
- `cloud-backend/app/models/provider_call_log.py`（新文件）
- `cloud-backend/app/models/__init__.py`

cloud-backend Schema：
- `cloud-backend/app/schemas/usage.py`（新文件）
- `cloud-backend/app/schemas/provider_log.py`（新文件）
- `cloud-backend/app/schemas/__init__.py`

cloud-backend API：
- `cloud-backend/app/api/v1/usage.py`（新文件）
- `cloud-backend/app/api/v1/provider_log.py`（新文件）
- `cloud-backend/app/main.py`

cloud-backend 服务：
- `cloud-backend/app/services/usage_service.py`（新文件）
- `cloud-backend/app/services/provider_log_service.py`（新文件）

cloud-backend 迁移：
- `cloud-backend/migrations/ddl/005_usage_events.sql`（新文件）
- `cloud-backend/migrations/ddl/006_provider_call_log.sql`（新文件）

cloud-backend 测试：
- `cloud-backend/tests/test_usage.py`（新文件）
- `cloud-backend/tests/test_provider_call_log.py`（新文件）

任务管理：
- `tasks/current-task.md`

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `cloud-backend/app/providers/` 下所有文件
- `cloud-backend/app/api/v1/auth.py` — Auth 核心逻辑
- `cloud-backend/app/api/v1/devices.py` — Device 核心逻辑
- `cloud-backend/app/api/deps.py` — 鉴权链
- `cloud-backend/app/core/security.py` — Token 逻辑
- `cloud-backend/app/core/config.py` — 配置
- `cloud-backend/app/models/user.py` — 已有模型
- `cloud-backend/app/models/device.py` — 已有模型
- `cloud-backend/app/models/auth_session.py` — 已有模型
- `cloud-backend/app/models/risk_log.py` — 已有模型
- `cloud-backend/app/services/auth_service.py`
- `cloud-backend/app/services/device_service.py`
- `cloud-backend/migrations/ddl/001_users.sql` 至 `004_risk_logs.sql`
- `desktop-app/` 下所有文件
- `docs/05-api-contract.md`
- `docs/12-database-design.md`
- shared DTO / OpenAPI 文件
- Tauri 权限配置

## 新增依赖申请

无新增依赖。使用已有 `fastapi`、`sqlalchemy`、`pydantic`、`asyncpg`、`pytest` 等现有依赖栈。

## 验收标准

### 表结构
- ✅ `usage_events` 表创建成功，包含所有必需字段
- ✅ `provider_call_log` 表创建成功，包含所有必需字段
- ✅ 索引覆盖 user_id、device_id、feature、created_at 等常用查询字段
- ✅ 字段类型与现有 models 风格一致（UUID PK、VARCHAR、JSONB、TIMESTAMPTZ）

### 写入
- ✅ 可通过 service 层写入 usage_events 记录
- ✅ 可通过 service 层写入 provider_call_log 成功记录（status=success）
- ✅ 可通过 service 层写入 provider_call_log 失败记录（status=error，含 error_code）
- ✅ metadata_json 不保存 Token、API Key、图片原文、OCR 全文等敏感内容

### 查询 API
- ✅ `GET /api/v1/usage/events` 返回用户自己的使用事件
- ✅ `GET /api/v1/provider-call-logs` 返回用户自己的调用日志
- ✅ 支持分页（limit/offset）
- ✅ 支持按 feature 筛选
- ✅ provider-call-logs 支持按 status 筛选
- ✅ 响应格式遵循统一 response shape

### 鉴权与安全
- ✅ 无 token → 401 AUTH_REQUIRED
- ✅ 用户 A 不能查询用户 B 的数据
- ✅ 不暴露 Token、API Key、用户密码等敏感信息

## 测试方式

必须至少提供：

1. 表结构测试（2 个）：
   - usage_events 表存在、列正确
   - provider_call_log 表存在、列正确

2. 写入测试（3 个）：
   - record_usage_event 写入成功
   - record_provider_call 成功记录
   - record_provider_call 失败记录（含 error_code）

3. 查询鉴权测试（2 个）：
   - 无 token 访问受保护端点 → 401
   - 用户 A 不能查询用户 B 的数据

4. 查询功能测试（2 个）：
   - 分页 + feature 筛选正常
   - provider-call-logs status 筛选正常

5. 敏感字段测试（1 个）：
   - metadata_json 不含敏感信息

目标：≥ 10 个测试用例，100% 通过。

## 是否允许新增依赖

否。仅使用已有依赖栈。

## 是否涉及重大变更

是（数据库 schema 变更 — 新建 2 张 PostgreSQL 表）。

原因：本任务新建云端 PostgreSQL 表 `usage_events` 和 `provider_call_log`，按 `CODEX.md:34` "修改数据库表结构" 属于重大变更。用户已明确确认本任务范围。

| 维度 | 说明 |
|------|------|
| 变更类型 | 新建 PostgreSQL 表（`usage_events`、`provider_call_log`），不修改已有表 |
| 影响范围 | `cloud-backend/migrations/ddl/`（新 DDL）、`cloud-backend/app/models/`（新模型） |
| 是否影响云端 | 是，在 cloud-backend PostgreSQL 中新增 2 张表 |
| 是否影响 API 契约 | 新增 2 个 GET 查询端点，不修改已有端点 |
| 是否影响 Provider 接口 | 否。Provider 接口定义不变 |
| 是否影响授权/Token | 否。仅读取已有 user_id/device_id |
| 是否需要数据库迁移 | 是。通过 DDL 文件（`005_usage_events.sql`、`006_provider_call_log.sql`）执行 |
| 是否兼容旧版本 | 是。新表为独立新建，不影响已有 4 张表 |

风险点：
- 新表写入可能影响数据库性能（初期数据量小，影响可忽略）
- `estimated_cost` 字段后续需要成本换算逻辑（本任务仅预留字段）

回滚方案：
- 通过 Git 分支回滚（`feature/sprint-01-usage-provider-log`）
- DDL 中包含 DROP TABLE 语句用于回滚

## 给 Codex Review 的审查指令

请审查 Task-05 使用统计基础表 + provider_call_log 表任务单。

### 重点检查

1. ✅ 任务范围是否只做基础表 + 最小查询（不做真实 AI 调用/扣费/报表）
2. ✅ "允许修改哪些文件" 是否仅限 cloud-backend 模型/API/schema/service/migration/test
3. ✅ "禁止修改哪些文件" 是否覆盖了 Provider 接口、Auth/Device 核心、desktop-app
4. ✅ usage_events 字段是否满足使用统计需求
5. ✅ provider_call_log 字段是否满足 Provider 审计需求
6. ✅ metadata_json 安全约束是否明确
7. ✅ API 是否要求鉴权、用户隔离
8. ✅ 是否涉及重大变更（是，新建 2 张 PostgreSQL 表）
9. ✅ 是否无新增依赖
10. ✅ "本次不开发什么" 是否覆盖了 BACKLOG / P1 / FUTURE 功能

输出：
- 任务单结构完整性
- 范围越界检查
- 安全风险检查
- 验收标准完整性
- 任务单是否批准
