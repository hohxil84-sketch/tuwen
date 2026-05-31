# 当前任务：Sprint-02 Task-01 PostgreSQL 集成测试基础设施

## 状态

`MVP_REQUIRED` — 由 CC 实现，Codex Review。

## 建议分支

`feature/sprint-02-task-01-pg-integration-test`，基于 `main` 当前最新提交。

## 前置任务

- Sprint-01 Task-01 ~ Task-06 已全部合并到 `main`。
- 现有 DDL 文件：`001_users.sql` ~ `006_provider_call_log.sql`。
- 测试框架当前仅使用 SQLite 内存数据库（`tests/conftest.py`）。
- 现有 SQLite ORM 测试当前通过 `79 passed`。

## 背景

Sprint-01 期间新建了 6 张表的 DDL，但所有测试都在 SQLite 内存数据库上运行。SQLite 与 PostgreSQL 在 DDL 约束（CHECK、FK、数据类型）、默认值函数（`gen_random_uuid()` vs SQLite hex）、索引行为等方面存在差异。在继续建新表之前，需要建立 PostgreSQL 集成测试基础设施，确保现有 DDL 在目标数据库中可正确执行，并为后续 credit、Provider 等模块提供可复用的 PG 测试基座。

本任务是纯测试基础设施任务，**不新建业务表、不修改 DDL、不实现 Provider**。

## Sprint-02 任务拆分说明

按 Codex 建议，原合并任务单已拆分为三个独立任务：

| 任务 | 范围 | 依赖 |
|------|------|------|
| **Task-01（本任务）** | PostgreSQL 集成测试基础设施 | 无 |
| Task-02（后续） | `credit_accounts` + `credit_ledger` 基础表 | Task-01 PG 测试基座 |
| Task-03（后续） | `BaseProvider` 正式化 + `MockProvider` | Task-02 credit 表 + Task-01 PG 测试基座 |

Task-03 需额外注意：`ProviderResult` 字段必须与 `provider_call_log` 字段保持清晰映射关系：
- `prompt_tokens` ← `input_units`（输入 token 数）
- `completion_tokens` ← `output_units`（输出 token 数）
- `total_tokens` = `input_units + output_units`
- `estimated_cost` ← `cost_service.estimate_cost()` 计算结果
- `latency_ms` ← Provider 调用计时
- 该映射将在 Task-03 任务单中详细定义。

## 本次只开发什么

### 1. PostgreSQL 集成测试 fixture（conftest_pg.py）

新建 `cloud-backend/tests/conftest_pg.py`：

- 读取环境变量 `TEST_DATABASE_URL`（如 `postgresql+asyncpg://postgres:test@localhost:5432/postgres`）。
- 如果环境变量未设置，session 级 fixture 调用 `pytest.skip("TEST_DATABASE_URL not set")`，**不阻止无 PG 环境时的 SQLite 测试**。
- Session 级 fixture：
  - 创建 async SQLAlchemy engine（连接真实 PostgreSQL）。
  - 按编号顺序执行 `cloud-backend/migrations/ddl/*.sql` 文件（`001` → `006`）。
  - yield engine。
  - teardown 时执行 DDL 文件中注释形式的 `DROP TABLE IF EXISTS`（按逆序），清理测试表。
  - dispose engine。
- Function 级 fixture：
  - 每个测试用例在自己的事务中运行，测试结束后 rollback。
  - 模式参考现有 `tests/conftest.py` 的 `db_session` fixture。

### 2. DDL 集成测试（test_migrations_integration.py）

新建 `cloud-backend/tests/test_migrations_integration.py`：

- 所有测试依赖 `conftest_pg.py` 的 PG fixture；未设置 `TEST_DATABASE_URL` 时自动 skip。
- 测试用例：

  #### 2a. 表存在性测试
  - 验证全部 6 张表（`users`、`devices`、`auth_sessions`、`risk_logs`、`usage_events`、`provider_call_log`）在 PostgreSQL 中成功创建。

  #### 2b. 列完整性测试
  - 对每张表，通过 `information_schema.columns` 验证所有必需列存在且数据类型正确。

  #### 2c. CHECK 约束生效测试
  - 对 `provider_call_log` 表：插入 `status='pending'`（非法值）→ PostgreSQL 报错 `check constraint`。
  - 对 `provider_call_log` 表：插入 `prompt_tokens=-1`（非法值）→ PostgreSQL 报错。
  - 验证 CHECK 约束名字与 DDL 中定义一致（如 `chk_provider_call_log_status`）。
  - 对每张有 CHECK 约束的表至少验证 1 条。

  #### 2d. FK 约束测试
  - 向 `devices` 表插入 `user_id` 为不存在 UUID → PostgreSQL 报错 `foreign key constraint`。

  #### 2e. 降级路径验证
  - 验证每个 DDL 文件末尾存在 `DROP TABLE IF EXISTS <table_name>` 注释行。
  - 验证该语句语法正确：在 tearDown 中按逆序执行这些 DROP 语句，确认 PostgreSQL 不报错。
  - **说明**：这不是真实的 migration rollback 测试（本任务不引入 migration 框架），只验证降级路径可执行。

### 3. CI / 本地运行说明

- 在 `cloud-backend/docs/` 新增 `pg-integration-test-guide.md`（或追加到现有文档）：
  - 本地启动测试 PG：`docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16`
  - 运行集成测试：`TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres pytest tests/test_migrations_integration.py -v`
  - 运行全部测试（含集成）：同上命令
  - 仅运行 SQLite 测试（无 PG 时默认行为）：`pytest tests/ -v --ignore=tests/test_migrations_integration.py`
  - 清理 PG 容器：`docker rm -f pg-test`
  - 说明 `TEST_DATABASE_URL` 为空时集成测试自动 skip，不影响日常开发。

### 4. 现有测试不回归

- `pytest tests/ -v --ignore=tests/test_migrations_integration.py` 继续通过（目标 ≥ 79 passed）。
- `git diff --check` 通过。

## 本次不开发什么

- ❌ 不新建业务表（`credit_accounts`、`credit_ledger` 等）。
- ❌ 不修改已有 DDL 文件（`001_users.sql` ~ `006_provider_call_log.sql`）。
- ❌ 不实现 Provider 抽象、MockProvider、BaseProvider。
- ❌ 不实现 credit_service、cost_service。
- ❌ 不新增 API 端点。
- ❌ 不修改 API 契约（`docs/05-api-contract.md`）。
- ❌ 不修改 OpenAPI / shared DTO。
- ❌ 不调用真实 AI API。
- ❌ 不修改 Auth/Device 核心逻辑。
- ❌ 不修改 Tauri 权限或 desktop-app。
- ❌ 不新增前端页面。
- ❌ 不新增 Python 依赖（`asyncpg` 已在依赖栈中）。
- ❌ 不实现 BACKLOG / FUTURE 功能。

## 允许修改哪些文件

- `cloud-backend/tests/conftest_pg.py`（新文件）
- `cloud-backend/tests/test_migrations_integration.py`（新文件）
- `cloud-backend/docs/pg-integration-test-guide.md`（新文件）
- `tasks/current-task.md`

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `cloud-backend/app/**`（所有业务代码）
- `cloud-backend/migrations/ddl/*.sql`（已有 DDL 文件）
- `cloud-backend/tests/conftest.py`（现有 SQLite fixture）
- `cloud-backend/tests/test_*.py`（除 `test_migrations_integration.py` 外的已有测试）
- `desktop-app/**`
- `shared/**`（含 OpenAPI、DTO、TypeScript 类型）
- `official-website/**`
- `tools/**`
- `.github/**`
- `docs/05-api-contract.md`
- `docs/13-module-roadmap.md`
- 任何依赖配置文件（`requirements.txt`、`pyproject.toml`、`package.json` 等）
- 任何锁文件
- `.env` / `.env.example`

## 验收标准

- ✅ `tests/conftest_pg.py` 存在，`TEST_DATABASE_URL` 未设置时 session fixture 自动 skip。
- ✅ `tests/test_migrations_integration.py` 存在，覆盖：
  - 全部 6 张表存在性。
  - 每张表列完整性（名称 + 类型）。
  - CHECK 约束生效（至少覆盖 `provider_call_log` 的 status/tokens 约束）。
  - FK 约束生效（至少 `devices.user_id → users.id`）。
  - DDL 文件降级注释存在且可执行。
- ✅ 设置 `TEST_DATABASE_URL` 后集成测试全部通过。
- ✅ 未设置 `TEST_DATABASE_URL` 时所有集成测试自动 skip。
- ✅ 现有 SQLite 测试无回归（`pytest tests/ -v --ignore=tests/test_migrations_integration.py` 全部通过）。
- ✅ `git diff --check` 通过。

## 测试方式

### SQLite 测试（必须，无 PG 环境）

```bash
cd cloud-backend
pytest tests/ -v --ignore=tests/test_migrations_integration.py
```

### PostgreSQL 集成测试（条件执行）

```bash
# 1. 启动测试 PG
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

# 2. 等待 PG 就绪
until docker exec pg-test pg_isready -U postgres; do sleep 1; done

# 3. 运行集成测试
cd cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/test_migrations_integration.py -v

# 4. 运行全部测试（SQLite + PG）
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  pytest tests/ -v

# 5. 清理
docker rm -f pg-test
```

### 静态检查

```bash
cd D:/Project/ad-assistant
git status --short --branch
git diff --check
```

## 是否允许新增依赖

**否**。已有依赖栈中 `asyncpg` 已安装，无需新增。

## 是否涉及重大变更

**否**。

本任务只新增测试文件，不修改数据库 schema、API 实现、Provider 接口、Auth/Token、扣费、支付、Tauri 权限或本地服务启动方式。

## 安全检查

- 本任务为纯测试基础设施，无安全风险。
- 测试 PG 连接使用本地 Docker 容器，不连接外部数据库。
- 测试环境变量 `TEST_DATABASE_URL` 不得包含生产数据库凭证。
- 不下发 API Key、不修改权限、不绕过授权。
- 不新增远程命令执行能力。

## 后续候选任务

以下任务不在本任务范围内，仅作为 Sprint-02 后续计划参考：

- **Task-02（候选）**：`credit_accounts` + `credit_ledger` 基础表、模型、schema、查询 API（`GET /api/v1/credits/balance`、`GET /api/v1/credits/ledger`）。
- **Task-03（候选）**：`BaseProvider` 正式化 + `MockProvider` + `cost_service` + mock call 端点（`POST /api/v1/providers/mock/call`）。

Task-03 的 `ProviderResult` 字段必须与 `provider_call_log` 建立明确映射：

| ProviderResult 字段 | provider_call_log 字段 | 说明 |
|---------------------|------------------------|------|
| `input_units` | `prompt_tokens` | 输入 token 数 |
| `output_units` | `completion_tokens` | 输出 token 数 |
| `input_units + output_units` | `total_tokens` | 总计 |
| `image_units` | 无直接映射 | 图片数，记录到 `metadata_json` 或后续扩展 |
| `gpu_seconds` | 无直接映射 | GPU 时间，记录到 `metadata_json` 或后续扩展 |
| `estimated_cost` | `estimated_cost` | 成本估算（由 `cost_service` 计算） |
| `currency` | 无直接映射 | 币种（默认 CNY），影响 `estimated_cost` 计算 |
| `result` | 不存储 | 业务结果返回调用方 |
| `raw_usage` | 不存储 | 原始 usage 供调试，不落库 |

## 给 Codex Review 的审查指引

请审查 Sprint-02 Task-01 PostgreSQL 集成测试基础设施。

重点检查：

1. 任务范围是否只做 PG 集成测试基础设施（不建新表、不写 Provider、不改 DDL）。
2. `conftest_pg.py` 是否正确处理 `TEST_DATABASE_URL` 未设置时的 skip 逻辑。
3. DDL 执行顺序是否正确（`001` → `006`），teardown 逆序是否正确。
4. 集成测试是否覆盖表存在性、列完整性、CHECK 约束、FK 约束、降级路径。
5. 现有 SQLite 测试是否不受影响（`--ignore` 模式）。
6. 是否无新增依赖。
7. 是否不修改 OpenAPI / shared DTO / API 契约。
8. 后续候选任务说明是否清晰、不越界。

输出：

- 任务单结构完整性
- 范围越界检查
- 测试覆盖评估
- 安全风险检查
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
