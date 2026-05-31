# 当前任务：Sprint-02 Task-01 AI 算力账户 + Provider 抽象 + PostgreSQL 集成测试基础设施

## 状态

`MVP_REQUIRED` — 由 CC 实现，Codex Review。

## 建议分支

`feature/sprint-02-task-01-credit-provider`，基于 `main` 当前最新提交。

## 前置任务

- Sprint-01 Task-01 ~ Task-06 已全部合并到 `main`。
- `usage_events` 表已存在（Task-05）。
- `provider_call_log` 表已存在（Task-05）。
- Provider 层目前只有骨架占位（`cloud-backend/app/providers/base.py`、`__init__.py`）。
- 测试框架当前仅使用 SQLite 内存数据库（`tests/conftest.py`）。

## 背景

Sprint-01 完成了 Auth/Device、本地 OCR、usage_events 和 provider_call_log 基础表。Sprint-02 需要推进云端 AI 算力的核心闭环：需要有用户额度账户来管理可用算力，需要有 credit_ledger 来记录每一笔额度变动，需要 Provider 抽象能产出 `estimated_cost` 并写入 `provider_call_log`，还需要 PostgreSQL 集成测试基础设施来验证 DDL 在真实数据库中的行为。

本轮只建表、建 Provider 抽象和模拟 Provider、建 PostgreSQL 测试基础设施，**不做真实 AI Provider 调用、不做真实扣费、不做支付/充值/赠送**。

## 本次只开发什么

### 子任务 A：credit_accounts 和 credit_ledger 基础表

#### A1. credit_accounts 表

新建 `credit_accounts` 表，记录每个用户的 AI 算力账户。

最低字段：
- `id` UUID PRIMARY KEY
- `user_id` UUID → users(id) NOT NULL UNIQUE（一个用户一个账户）
- `balance` INTEGER NOT NULL DEFAULT 0（当前可用 AI 算力点数）
- `frozen` INTEGER NOT NULL DEFAULT 0（冻结中的点数，预留字段）
- `version` INTEGER NOT NULL DEFAULT 1（乐观锁版本号）
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

约束：
- `balance >= 0` CHECK
- `frozen >= 0` CHECK
- `user_id` UNIQUE

#### A2. credit_ledger 表

新建 `credit_ledger` 表，记录每一笔额度变动明细（不可变日志）。

最低字段：
- `id` UUID PRIMARY KEY
- `user_id` UUID → users(id) NOT NULL（所属用户）
- `account_id` UUID → credit_accounts(id) NOT NULL（关联账户）
- `type` VARCHAR NOT NULL（操作类型：`CHARGE`/`DEDUCT`/`FREEZE`/`UNFREEZE`/`REFUND`/`ADJUST`）
- `amount` INTEGER NOT NULL（变动金额，正数为增加，负数为扣减）
- `balance_before` INTEGER NOT NULL（变动前余额）
- `balance_after` INTEGER NOT NULL（变动后余额）
- `reference_type` VARCHAR（关联来源类型：`provider_call`/`admin_adjust`/`recharge`，可为空）
- `reference_id` VARCHAR（关联来源 ID，如 `provider_call_log.id`，可为空）
- `note` TEXT（备注，可为空）
- `operator` VARCHAR（操作者：`system`/`admin:<admin_id>`，不可为空）
- `request_id` VARCHAR（关联 API 请求 ID，可为空）
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

约束：
- `type` CHECK IN ('CHARGE', 'DEDUCT', 'FREEZE', 'UNFREEZE', 'REFUND', 'ADJUST')
- `balance_before >= 0` CHECK
- `balance_after >= 0` CHECK
- `amount` 可为正或负，但 `type=DEDUCT` 时不允许正数（由 service 层校验，非 DDL 约束）

索引：
- `idx_credit_ledger_user_id` ON (user_id, created_at DESC)
- `idx_credit_ledger_account_id` ON (account_id, created_at DESC)

#### A3. 后端模型 / Schema / Service

- 新建 `CreditAccount` ORM 模型。
- 新建 `CreditLedger` ORM 模型。
- 新建 `credit_accounts` Schema（Pydantic request/response DTO）。
- 新建 `credit_ledger` Schema（Pydantic request/response DTO）。
- 新建 `credit_service.py`：
  - `get_credit_account(db, user_id) -> dict` — 查询用户信用账户。
  - `list_credit_ledger(db, user_id, limit, offset) -> dict` — 查询用户额度变动明细。
- **本次不实现 `deduct_credits()`**（扣费逻辑需要 Provider 调用链路完成后再做）。

#### A4. 查询 API

- `GET /api/v1/credits/balance` — 查询当前用户的 AI 算力余额。
  - 必须鉴权。
  - 普通用户只能查询自己的账户。
  - 如果用户没有 account 记录，自动返回 `balance=0`（不自动创建账户）。
  - 返回统一结构 `{success, data, error, request_id}`。

- `GET /api/v1/credits/ledger?limit=50&offset=0` — 查询当前用户的额度变动明细。
  - 必须鉴权。
  - 普通用户只能查询自己的 ledger。
  - 按 `created_at` 倒序。
  - 返回统一结构 `{success, data, error, request_id}`。

#### A5. DDL 迁移文件

- 新建 `cloud-backend/migrations/ddl/007_credit_accounts.sql`
- 新建 `cloud-backend/migrations/ddl/008_credit_ledger.sql`
- 每个 DDL 文件末尾包含回滚注释 `DROP TABLE IF EXISTS <table_name>;`

### 子任务 B：云端 Provider 抽象与模拟 Provider 调用

#### B1. Provider 基类正式化

当前 `cloud-backend/app/providers/base.py` 只有注释占位。本任务将其正式化为可用的抽象基类/协议：

- 定义 `BaseProvider` 抽象基类，要求子类实现：
  - `async call(*, feature, model, input_data, user_id, device_id, request_id) -> ProviderResult`
- 定义 `ProviderResult` Pydantic model / dataclass，字段对齐 `provider_call_log` 和 README 描述的 Provider 返回结构：
  - `provider: str`
  - `model: str`
  - `input_units: int`
  - `output_units: int`
  - `image_units: int`
  - `gpu_seconds: float`
  - `raw_cost: float`
  - `estimated_cost: float`
  - `currency: str`（默认 `"CNY"`）
  - `result: dict`
  - `raw_usage: dict`
- 定义 `ProviderError` 异常类，包含 `error_code: str` 和 `message: str`。

#### B2. 模拟 Provider 实现

新建 `MockProvider`，不调用任何外部 AI API：

- `call()` 方法：
  - 根据 `feature` 返回预设的模拟结果（OCR → 模拟识别文本，vectorize → 模拟矢量路径）。
  - 生成模拟的 token/耗时/cost 数据。
  - 延迟 10-50ms 模拟网络调用。
- 成功调用时：
  - 内部调用 `record_provider_call()` 写入 `provider_call_log`（status=success）。
  - 设置 `estimated_cost=0.001`（模拟 0.1 分钱成本）。
- 错误模拟：
  - 支持特殊输入触发失败（如 `input_data={"simulate_error": "timeout"}`）。
  - 失败时写入 `provider_call_log`（status=error，含 error_code）。

#### B3. Provider 路由入口

新建 `MockProvider` 的调用端点，用于验证端到端链路：

- `POST /api/v1/providers/mock/call`
  - 必须鉴权。
  - 请求 body：`{feature, model, input_data}`
  - 调用 `MockProvider.call()`。
  - 成功后写入 `provider_call_log`。
  - 返回 `{provider, model, result, estimated_cost, credits_charged}`。
  - 返回统一结构 `{success, data, error, request_id}`。

#### B4. 成本估算工具

- 新建 `cloud-backend/app/services/cost_service.py`：
  - `estimate_cost(provider, model, prompt_tokens, completion_tokens, image_units, gpu_seconds) -> float`
  - 定义不同 Provider/Model 的估算价格常量（如 deepseek-chat: ¥0.001/1K tokens）。
  - 返回 CNY 估算成本。
  - 这是估算，不代表真实 Provider 账单。

### 子任务 C：PostgreSQL 集成测试基础设施

#### C1. 集成测试配置

- 新建 `cloud-backend/tests/conftest_pg.py`：
  - 使用 `TEST_DATABASE_URL` 环境变量连接真实 PostgreSQL。
  - 如果没有设置环境变量，fixture 触发 `pytest.skip`。
  - Session 级 fixture：创建 engine、运行 DDL、yield、dispose。
  - Function 级 fixture：事务回滚（类似现有 SQLite conftest 模式）。

#### C2. DDL 集成测试

- 新建 `cloud-backend/tests/test_migrations_integration.py`：
  - 连接到真实 PostgreSQL 后，执行所有 DDL 文件。
  - 验证所有表存在且列正确。
  - 验证 CHECK 约束能被 PostgreSQL 遵守（插入非法数据 → 报错）。
  - 验证 DDL 中所有 `DROP TABLE IF EXISTS` 注释能正常执行（回滚测试）。
  - 如果 `TEST_DATABASE_URL` 未设置，测试自动 skip。

#### C3. CI 集成指引

- 在 `docs/` 新增或更新文档说明如何在本地和 CI 环境中运行 PostgreSQL 集成测试：
  - Docker Compose 配置推荐（`docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16`）。
  - 环境变量设置方式。
  - 现有 SQLite 测试和 PG 集成测试的区别和运行方式。

### 子任务 D：文档同步

- 更新 `docs/05-api-contract.md`：补充 Credit API（`GET /api/v1/credits/balance`、`GET /api/v1/credits/ledger`）和 Mock Provider API（`POST /api/v1/providers/mock/call`）。
- 更新 `docs/13-module-roadmap.md`：Sprint-02 状态备注。
- 更新 `docs/sprint-01-summary.md`：当前 Sprint-02 Task-01 已启动备注（可选，不强制）。

## 本次不开发什么

- ❌ 不调用真实 OpenAI / Claude / DeepSeek / 图片 Provider。
- ❌ 不把 API Key 发给客户端。
- ❌ 不实现真实扣费逻辑（`deduct_credits()` 留到后续任务）。
- ❌ 不实现会员、套餐、支付、充值、赠送额度。
- ❌ 不实现后台管理系统。
- ❌ 不实现复杂报表或数据看板。
- ❌ 不修改 Auth/Device 核心逻辑（仅读取 user_id）。
- ❌ 不修改 Tauri 权限或桌面端代码。
- ❌ 不修改 desktop-app 业务代码。
- ❌ 不新增前端页面。
- ❌ 不修改 `shared/` DTO 或 OpenAPI 文件（除非与本次 API 契约强相关且用户已确认）。
- ❌ 不实现 BACKLOG / FUTURE 功能。
- ❌ 不引入大型第三方依赖。

## 允许修改哪些文件

允许在确认后修改：

### 子任务 A（credit 表）
- `cloud-backend/app/models/credit_account.py`（新文件）
- `cloud-backend/app/models/credit_ledger.py`（新文件）
- `cloud-backend/app/models/__init__.py`
- `cloud-backend/app/schemas/credit.py`（新文件）
- `cloud-backend/app/schemas/__init__.py`
- `cloud-backend/app/services/credit_service.py`（新文件）
- `cloud-backend/app/api/v1/credit.py`（新文件）
- `cloud-backend/app/main.py`
- `cloud-backend/migrations/ddl/007_credit_accounts.sql`（新文件）
- `cloud-backend/migrations/ddl/008_credit_ledger.sql`（新文件）

### 子任务 B（Provider）
- `cloud-backend/app/providers/base.py`（修改：从占位变为正式抽象基类）
- `cloud-backend/app/providers/mock_provider.py`（新文件）
- `cloud-backend/app/providers/__init__.py`
- `cloud-backend/app/schemas/provider.py`（新文件）
- `cloud-backend/app/services/cost_service.py`（新文件）
- `cloud-backend/app/api/v1/provider_call.py`（新文件）
- `cloud-backend/app/main.py`

### 子任务 C（集成测试）
- `cloud-backend/tests/conftest_pg.py`（新文件）
- `cloud-backend/tests/test_migrations_integration.py`（新文件）
- `docs/` 下集成测试说明文档（新文件或现有文档追加）

### 子任务 D（文档）
- `docs/05-api-contract.md`
- `docs/13-module-roadmap.md`
- `tasks/current-task.md`

### 测试文件
- `cloud-backend/tests/test_credit.py`（新文件）
- `cloud-backend/tests/test_provider.py`（新文件）

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `desktop-app/**`
- `shared/**`
- `official-website/**`
- `tools/**`
- `.github/**`
- `cloud-backend/app/api/v1/auth.py` — Auth 核心逻辑
- `cloud-backend/app/api/v1/devices.py` — Device 核心逻辑
- `cloud-backend/app/api/deps.py` — 鉴权链（但可读取依赖/新增 deps 函数，不修改现有逻辑）
- `cloud-backend/app/core/security.py` — Token 逻辑
- `cloud-backend/app/core/config.py` — 配置（仅追加环境配置，不修改现有）
- `cloud-backend/app/models/user.py`
- `cloud-backend/app/models/device.py`
- `cloud-backend/app/models/auth_session.py`
- `cloud-backend/app/models/risk_log.py`
- `cloud-backend/app/models/usage_event.py`
- `cloud-backend/app/models/provider_call_log.py`
- `cloud-backend/app/services/auth_service.py`
- `cloud-backend/app/services/device_service.py`
- `cloud-backend/app/services/usage_service.py`
- `cloud-backend/app/services/provider_log_service.py`
- `cloud-backend/migrations/ddl/001_users.sql` ~ `006_provider_call_log.sql`
- 任何依赖配置文件（`requirements.txt`、`pyproject.toml`、`package.json` 等）
- 任何锁文件
- `.env` / `.env.example`

## 验收标准

### 子任务 A
- ✅ `credit_accounts` 表创建成功，包含所有必需字段和约束。
- ✅ `credit_ledger` 表创建成功，包含所有必需字段和约束。
- ✅ `GET /api/v1/credits/balance` 返回用户余额（无账户时 balance=0）。
- ✅ `GET /api/v1/credits/ledger` 返回额度变动明细，支持分页。
- ✅ 鉴权正确：无 token → 401，用户 A 不能查用户 B 的数据。

### 子任务 B
- ✅ `BaseProvider` 抽象基类定义完整，包含 `call()` 和 `ProviderResult`。
- ✅ `MockProvider` 能成功调用并返回模拟结果。
- ✅ `MockProvider` 调用后 `provider_call_log` 中存在对应记录。
- ✅ `MockProvider` 错误模拟能记录 status=error 和 error_code。
- ✅ `POST /api/v1/providers/mock/call` 端点正常工作，返回统一结构。
- ✅ `cost_service.estimate_cost()` 能对不同 provider/model 返回合理估算。

### 子任务 C
- ✅ `tests/conftest_pg.py` 存在，`TEST_DATABASE_URL` 未设置时自动 skip。
- ✅ `tests/test_migrations_integration.py` 存在，覆盖所有 DDL 文件的列和约束验证。
- ✅ DDL 回滚注释能成功执行 `DROP TABLE`。
- ✅ 现有 SQLite 测试（`pytest tests/ -v`）继续全部通过，无回归。

### 通用
- ✅ 所有新 API 遵循统一响应结构 `{success, data, error, request_id}`。
- ✅ `git diff --check` 通过。
- ✅ 无新增外部依赖。

## 测试方式

### SQLite ORM 测试（必须）

```bash
cd cloud-backend
pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

目标：所有非集成测试通过。

### PostgreSQL 集成测试（条件执行）

```bash
# 启动测试 PG
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

# 运行集成测试
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/test_migrations_integration.py -v

# 清理
docker rm -f pg-test
```

### 静态检查

```bash
git status --short --branch
git diff --check
```

## 是否允许新增依赖

**否**。使用已有依赖栈（`fastapi`、`sqlalchemy[asyncio]`、`pydantic`、`asyncpg`、`pytest`、`pytest-asyncio`、`httpx`、`aiosqlite`）。

如需新增依赖，先停止并说明原因，等待确认。

## 是否涉及重大变更

**是**。按 `CODEX.md` 定义，以下属于重大变更：

| 维度 | 说明 |
|------|------|
| 变更类型 | 新建 PostgreSQL 表（`credit_accounts`、`credit_ledger`）；修改 Provider 接口（从占位到正式抽象基类） |
| 影响范围 | `cloud-backend/migrations/ddl/`（新 DDL）、`cloud-backend/app/models/`（新模型）、`cloud-backend/app/providers/`（基类正式化） |
| 是否影响 API 契约 | 新增 3 个端点（credit/balance、credit/ledger、mock/call） |
| 是否影响授权/Token | 否。仅读取已有 user_id |
| 是否影响已有表结构 | 否。新建独立表，不修改已有 6 张表 |
| 是否需要数据库迁移 | 是。通过 DDL 文件（`007_credit_accounts.sql`、`008_credit_ledger.sql`）执行 |
| 是否兼容旧版本 | 是。新表为独立新建，不影响已有表 |
| 是否影响 Provider 接口 | 是。`base.py` 从注释占位变为正式抽象基类（向前兼容，无已有 Provider 实现需迁移） |

风险点：
- `credit_accounts` 和 `credit_ledger` 的乐观锁和并发扣费逻辑需要后续任务完善（本任务建表和基础查询）。
- Mock Provider 返回模拟数据，后续接入真实 Provider 时需要替换。
- PostgreSQL 集成测试依赖 Docker 环境，不是强制要求。

回滚方案：通过 Git 分支回滚（`feature/sprint-02-task-01-credit-provider`）。DDL 中包含 `DROP TABLE IF EXISTS` 注释用于数据库回滚。

## 安全检查

- 不下发 API Key 到客户端。
- 不由客户端扣点或计算 `estimated_cost`。
- 不由客户端决定套餐、权限或是否免费。
- 不绕过云端授权。
- 不保存明文 Token。
- `provider_call_log` 不记录 prompt 原文、图片原文、API Key。
- `credit_ledger.note` 不存储 Token、密码、完整隐私原文。
- 所有查询 API 必须鉴权且用户隔离。
- Mock Provider 不连接外部服务，无网络调用风险。
- 不新增远程命令执行能力。
- 不放宽文件系统权限。

## 给 Codex Review 的审查指引

请审查 Sprint-02 Task-01 AI 算力账户 + Provider 抽象 + PostgreSQL 集成测试基础设施。

重点检查：

1. 任务范围是否只做 credit 表、Provider 抽象、Mock Provider、PG 测试基础设施（不做真实 AI 调用/扣费/支付/充值）。
2. `credit_accounts` 和 `credit_ledger` 字段设计是否满足后续扣费需求。
3. `BaseProvider` 接口定义是否对齐项目统一 Provider 返回结构。
4. `MockProvider` 是否正确写入 `provider_call_log`。
5. `cost_service.estimate_cost()` 是否能被后续真实 Provider 复用。
6. 鉴权要求：credit 查询 API 是否强制鉴权且用户隔离。
7. 安全要求：`provider_call_log` 和 `credit_ledger` 不存储敏感内容。
8. PostgreSQL 集成测试是否仅在 `TEST_DATABASE_URL` 设定时运行，不影响现有 SQLite 测试。
9. 是否涉及重大变更及是否已在任务文档中明确记录。
10. 是否无新增外部依赖。

输出：

- 任务单结构完整性
- 范围越界检查
- 表结构设计合理性
- Provider 接口检查
- 安全风险检查
- PostgreSQL 集成测试基础设施检查
- 是否涉及重大变更确认
- 是否允许提交

## 完成输出要求

执行者完成后必须输出：

- 修改文件列表
- 实现内容（按子任务 A/B/C/D 分列）
- 未实现内容
- 测试命令和结果
- 风险点
- 是否触发重大变更
- 等待 Codex Review，不得自行提交
