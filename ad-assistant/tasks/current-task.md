# 当前任务：Sprint-02 Task-02 AI 算力账户与流水基础

## 状态

`MVP_REQUIRED` — 任务单待用户确认；确认后由 CC 实现，Codex Review。

## 建议分支

`feature/sprint-02-task-02-credit-ledger`，基于 `main` 当前最新提交。

## 前置任务

- Sprint-01 Task-01 ~ Task-06 已全部合并到 `main`。
- Sprint-02 Task-01 PostgreSQL 集成测试基础设施已合并到 `main`。
- 现有 DDL 文件：`001_users.sql` ~ `006_provider_call_log.sql`。
- 现有 PG 集成测试可验证 DDL 在真实 PostgreSQL 中执行。
- `docs/12-database-design.md` 已包含 `credit_accounts` 和 `credit_ledger` 草案。
- `docs/05-api-contract.md` 已列出 Credit API 草案：`GET /api/v1/credits/balance`。

## 背景

Sprint-01 已记录 usage_events 和 provider_call_log，但还没有用户 AI 算力账户与流水。后续 Provider 接入和真实扣费前，必须先有只由云端维护的余额表和流水表，保证扣费链路不会由客户端决定。

本任务只建立 **credit_accounts + credit_ledger 基础表、ORM、schema、service、只读查询 API 和测试**。本任务不做真实 Provider 调用，不做真实扣费，不做充值/支付，不做套餐发放自动化。

## 重大变更方案（需用户确认后才能执行）

本任务涉及数据库 schema、API 契约和 credit 逻辑，属于重大变更。用户确认本任务单后，才允许 CC 开始实现。

1. 修改原因
   - 为后续 AI 算力扣费、Provider 成本换算和用户余额查询提供最小基础。
   - 消除 Sprint-01 仅有 provider_call_log、无 credit_ledger 的缺口。

2. 风险点
   - 余额与流水字段若设计不严谨，后续扣费可能出现负数、重复记账或无法审计。
   - API 如果暴露写入能力，可能让客户端影响额度。
   - SQLite 与 PostgreSQL 数值/约束行为存在差异，需要继续用 PG 集成测试覆盖。

3. 影响范围
   - 新增 DDL：`credit_accounts`、`credit_ledger`。
   - 新增后端 ORM/schema/service/API。
   - 更新 API 文档中的 Credit API 描述。
   - 新增/更新后端测试和 PG 集成测试。

4. 回滚方案
   - 删除本任务新增 DDL 文件和新增后端文件。
   - 从 `app/main.py` 移除 credit router 注册。
   - 从 `app/models/__init__.py` 移除新增模型导入。
   - 通过 PR revert 回滚本任务 commit。

5. 是否兼容旧版本
   - 兼容。新增表和只读 API 不改变现有 Auth/Device/Usage/Provider Log 行为。
   - 不修改现有 001~006 DDL，不修改已有接口响应。

6. 是否需要数据库迁移
   - 需要新增 DDL 文件：`cloud-backend/migrations/ddl/007_credit_accounts.sql` 和 `008_credit_ledger.sql`。
   - 不引入 Alembic，不修改已有 DDL 文件。

## 本次只开发什么

### 1. 新增 PostgreSQL DDL

新增 `cloud-backend/migrations/ddl/007_credit_accounts.sql`：

- 表名：`credit_accounts`
- 字段：
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - `user_id UUID NOT NULL REFERENCES users(id)`
  - `plan_code VARCHAR(50) NOT NULL DEFAULT 'standard'`
  - `monthly_grant INTEGER NOT NULL DEFAULT 0`
  - `balance INTEGER NOT NULL DEFAULT 0`
  - `period_start TIMESTAMPTZ`
  - `period_end TIMESTAMPTZ`
  - `status VARCHAR(20) NOT NULL DEFAULT 'active'`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- 约束：
  - `user_id` 唯一，每个用户最多一个 active account 基础记录。
  - `monthly_grant >= 0`
  - `balance >= 0`
  - `status IN ('active', 'disabled')`
  - 若同时存在 `period_start` 和 `period_end`，则 `period_end > period_start`
- 索引：
  - `idx_credit_accounts_user_id`
  - `idx_credit_accounts_status`
- 文件末尾必须有注释形式 downgrade：
  - `-- DROP TABLE IF EXISTS credit_accounts CASCADE;`

新增 `cloud-backend/migrations/ddl/008_credit_ledger.sql`：

- 表名：`credit_ledger`
- 字段：
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - `user_id UUID NOT NULL REFERENCES users(id)`
  - `account_id UUID REFERENCES credit_accounts(id)`
  - `change_type VARCHAR(30) NOT NULL`
  - `amount INTEGER NOT NULL`
  - `balance_after INTEGER NOT NULL`
  - `source_type VARCHAR(50) NOT NULL`
  - `source_id VARCHAR(255)`
  - `description VARCHAR(255)`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- 约束：
  - `change_type IN ('grant', 'consume', 'refund', 'adjust')`
  - `amount <> 0`
  - `balance_after >= 0`
  - `source_type IN ('system', 'provider_call', 'manual', 'order')`
  - `consume` 类型必须 `amount < 0`
  - `grant`、`refund`、`adjust` 允许正负规则需在 service 中明确；本任务只要求 DB 保证非零和余额非负。
- 索引：
  - `idx_credit_ledger_user_id`
  - `idx_credit_ledger_account_id`
  - `idx_credit_ledger_created_at`
  - `idx_credit_ledger_change_type`
- 文件末尾必须有注释形式 downgrade：
  - `-- DROP TABLE IF EXISTS credit_ledger CASCADE;`

DDL 执行顺序必须是 `001` → `008`。不得修改 `001` ~ `006`。

### 2. 新增 ORM 模型

新增：

- `cloud-backend/app/models/credit_account.py`
- `cloud-backend/app/models/credit_ledger.py`

更新：

- `cloud-backend/app/models/__init__.py`

要求：

- ORM 字段与 DDL 保持一致。
- 使用现有 `Base`、UUID、时间字段风格。
- 不引入新依赖。
- 不把余额计算放到客户端。

### 3. 新增 schema

新增：

- `cloud-backend/app/schemas/credit.py`

至少包含：

- `CreditBalanceResponse`
  - `user_id`
  - `plan_code`
  - `monthly_grant`
  - `balance`
  - `period_start`
  - `period_end`
  - `status`
  - `updated_at`
- `CreditLedgerItem`
  - `id`
  - `user_id`
  - `change_type`
  - `amount`
  - `balance_after`
  - `source_type`
  - `source_id`
  - `description`
  - `created_at`
- `CreditLedgerListResponse`
  - `items`
  - `total`
  - `limit`
  - `offset`

### 4. 新增 credit service

新增：

- `cloud-backend/app/services/credit_service.py`

本任务只允许实现最小读写基础：

- `get_or_create_credit_account(db, user_id, plan_code='standard')`
  - 若账户不存在，创建余额为 0 的基础账户。
  - 不自动发放套餐额度。
  - 不读取客户端传入的余额。
- `get_credit_balance(db, user_id)`
  - 返回当前用户余额信息。
- `list_credit_ledger(db, user_id, limit=50, offset=0)`
  - 只查询当前用户自己的流水。
- 可选内部函数：`record_credit_ledger(...)`
  - 仅供测试和后续服务复用。
  - 必须校验 amount 非零、balance_after 非负、change_type/source_type 合法。
  - 本任务不得把它暴露成公共 API。

### 5. 新增只读 Credit API

新增：

- `cloud-backend/app/api/v1/credits.py`

更新：

- `cloud-backend/app/main.py`

API：

- `GET /api/v1/credits/balance`
  - 必须鉴权。
  - 只能返回当前登录用户自己的余额。
  - 若账户不存在，由 service 创建基础账户并返回。
  - 返回统一结构 `{success, data, error, request_id}`。
- `GET /api/v1/credits/ledger`
  - 必须鉴权。
  - 只能查询当前登录用户自己的流水。
  - 支持 `limit`、`offset`。
  - 按 `created_at` 倒序。
  - 返回统一结构 `{success, data, error, request_id}`。

禁止新增任何客户端可调用的扣费、充值、发放、调整余额 API。

### 6. 更新 API 文档

更新：

- `docs/05-api-contract.md`

要求：

- 明确 Credit API 当前仅有只读查询：
  - `GET /api/v1/credits/balance`
  - `GET /api/v1/credits/ledger`
- 明确客户端不得提交扣费结果、不得设置余额、不得创建流水。
- 文档不得声称已实现真实 Provider 扣费、充值、支付或套餐自动发放。

### 7. 新增/更新测试

新增：

- `cloud-backend/tests/test_credit.py`

更新：

- `cloud-backend/tests/test_migrations_integration.py`

测试覆盖：

- SQLite ORM/API 测试：
  - credit_accounts 表存在，字段匹配。
  - credit_ledger 表存在，字段匹配。
  - 未登录访问 balance/ledger 返回 401。
  - 登录用户只能看到自己的 balance/ledger。
  - 首次查询 balance 会创建基础账户，余额为 0。
  - ledger 支持分页，按时间倒序。
  - service 拒绝非法 change_type、source_type、amount=0、balance_after<0。
- PostgreSQL 集成测试：
  - 8 张表全部存在。
  - `credit_accounts` 和 `credit_ledger` 列完整且类型正确。
  - `credit_accounts.balance >= 0` CHECK 生效。
  - `credit_ledger.amount <> 0` CHECK 生效。
  - `credit_ledger.balance_after >= 0` CHECK 生效。
  - FK 约束生效。
  - 007/008 downgrade 注释存在且可执行。

## 本次不开发什么

- ❌ 不实现真实 AI Provider 调用。
- ❌ 不实现 `BaseProvider`、`MockProvider`、Provider 路由或 Provider 成本估算。
- ❌ 不实现真实扣费流程。
- ❌ 不实现充值、支付、订单、套餐购买、赠送额度。
- ❌ 不实现后台管理。
- ❌ 不新增前端页面。
- ❌ 不修改 desktop-app / Tauri 权限。
- ❌ 不修改 shared OpenAPI / DTO / TypeScript 类型。
- ❌ 不修改 Auth/Device/Token 核心逻辑。
- ❌ 不修改现有 `001` ~ `006` DDL。
- ❌ 不修改 `provider_call_log` 字段。
- ❌ 不新增依赖或升级依赖。
- ❌ 不实现 BACKLOG / FUTURE 功能。

## 允许修改哪些文件

- `cloud-backend/migrations/ddl/007_credit_accounts.sql`（新文件）
- `cloud-backend/migrations/ddl/008_credit_ledger.sql`（新文件）
- `cloud-backend/app/models/credit_account.py`（新文件）
- `cloud-backend/app/models/credit_ledger.py`（新文件）
- `cloud-backend/app/models/__init__.py`
- `cloud-backend/app/schemas/credit.py`（新文件）
- `cloud-backend/app/services/credit_service.py`（新文件）
- `cloud-backend/app/api/v1/credits.py`（新文件）
- `cloud-backend/app/main.py`（仅注册 credit router）
- `cloud-backend/tests/test_credit.py`（新文件）
- `cloud-backend/tests/test_migrations_integration.py`（仅扩展 007/008 覆盖）
- `docs/05-api-contract.md`（仅更新 Credit API 当前实现）
- `tasks/current-task.md`

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `cloud-backend/migrations/ddl/001_users.sql` ~ `006_provider_call_log.sql`
- `cloud-backend/app/providers/**`
- `cloud-backend/app/services/provider_log_service.py`
- `cloud-backend/app/services/usage_service.py`
- `cloud-backend/app/services/auth_service.py`
- `cloud-backend/app/services/device_service.py`
- `cloud-backend/app/api/v1/auth.py`
- `cloud-backend/app/api/v1/devices.py`
- `cloud-backend/app/api/v1/usage.py`
- `cloud-backend/app/api/v1/provider_log.py`
- `cloud-backend/tests/conftest.py`
- 既有 `cloud-backend/tests/test_auth.py`、`test_devices.py`、`test_usage.py`、`test_provider_call_log.py`
- `desktop-app/**`
- `shared/**`
- `official-website/**`
- `tools/**`
- `.github/**`
- 任何依赖配置文件（`requirements.txt`、`pyproject.toml`、`package.json` 等）
- 任何锁文件
- `.env` / `.env.example`

## 验收标准

- ✅ 新增 DDL 007/008，且不修改 001~006。
- ✅ `credit_accounts` 和 `credit_ledger` 在 SQLite ORM 测试和真实 PG 集成测试中通过。
- ✅ `GET /api/v1/credits/balance` 鉴权、用户隔离、首次自动创建基础账户。
- ✅ `GET /api/v1/credits/ledger` 鉴权、用户隔离、分页、倒序。
- ✅ 客户端没有任何可写余额/流水/扣费 API。
- ✅ service 层校验非法 change_type/source_type/amount/balance_after。
- ✅ `docs/05-api-contract.md` 与当前 Credit API 一致，不声称未实现能力。
- ✅ 无新增依赖。
- ✅ 无真实 AI 调用、无真实扣费、无支付/充值。
- ✅ SQLite 测试全部通过。
- ✅ PG 集成测试全部通过。
- ✅ `git diff --check` 通过。

## 测试方式

### SQLite 测试（必须）

```bash
cd cloud-backend
pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

### PostgreSQL 集成测试（必须）

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres \
  pytest tests/test_migrations_integration.py -v
```

如果本地 5433 不可用，可以使用任意本地测试 PostgreSQL，但必须在完成输出中写明实际 `TEST_DATABASE_URL`，且不得连接生产库。

### 全量测试（建议）

```bash
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres \
  pytest tests/ -v
```

### 静态检查

```bash
cd D:/Project/ad-assistant
git status --short --branch
git diff --check
```

## 是否允许新增依赖

**否**。

## 是否涉及重大变更

**是**。

涉及：

- 新增数据库表结构。
- 新增 Credit API。
- 新增 credit service 基础逻辑。

本任务单已经写明重大变更原因、风险、影响范围、回滚方案、兼容性和迁移方式。用户确认本任务单后，CC 才允许实现。

## 安全检查

- Credit 余额和流水只能由云端 service 维护。
- 客户端只能查询自己的余额和流水。
- 不允许客户端提交扣费结果。
- 不允许客户端设置余额。
- 不允许客户端创建流水。
- 不允许前端直连 Provider。
- 不下发 API Key、Token、密钥。
- 不保存明文 Token、密码或设备指纹。
- 不新增远程命令执行能力。
- 测试 PG 必须使用本地测试库，不得连接生产库。

## 后续候选任务

以下任务不在本任务范围内：

- **Task-03（候选）**：`BaseProvider` 正式化 + `MockProvider` + `cost_service`。
- **Task-04（候选）**：Provider mock call 记录 provider_call_log，但仍不接真实 AI。
- **Task-05（候选）**：真实扣费链路，把 provider_call_log 与 credit_ledger 串起来。
- **后续候选**：充值、支付、套餐发放、后台管理、成本报表。

Task-03 的 `ProviderResult` 字段仍需与 `provider_call_log` 保持明确映射，本任务不实现该映射代码。

## 给 Codex Review 的审查指引

请审查 Sprint-02 Task-02 AI 算力账户与流水基础。

重点检查：

1. 是否只实现 credit_accounts + credit_ledger 基础表、ORM、schema、service、只读 API 和测试。
2. 是否没有真实 Provider 调用、真实扣费、充值、支付、后台管理。
3. 是否没有客户端可写余额/流水/扣费 API。
4. DDL 约束是否覆盖余额非负、流水金额非零、状态/类型枚举、FK。
5. SQLite 测试和 PG 集成测试是否都覆盖新增表。
6. 用户隔离是否正确，普通用户只能查询自己的 credit 数据。
7. 是否无新增依赖。
8. 是否不修改 OpenAPI / shared DTO / desktop / Tauri。
9. 是否触发的重大变更均在本任务单范围内。

输出：

- 任务单结构完整性
- 范围越界检查
- 数据库/API/安全风险检查
- 测试覆盖评估
- 是否允许提交

## 完成输出要求

执行者完成后必须输出：

- 修改文件列表
- 实现内容
- 未实现内容
- 测试命令和结果（SQLite + PG 集成测试分别列出）
- 风险点
- 是否触发重大变更
- 等待 Codex Review，不得自行提交
