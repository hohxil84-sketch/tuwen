# Current Task: Sprint-02 Task-07 Backend PostgreSQL DateTime Alignment

## Status

`IMPLEMENTED_AWAITING_REVIEW`

Implementation completed on 2026-06-01. Waiting for Codex Review.

Branch: `feature/sprint-02-task-07-pg-datetime-align`
Base: `main` @ `afd1ca4` (PR #19 — docs: clarify Vite proxy API base URL)

## Suggested Branch

`feature/sprint-02-task-07-pg-datetime-align`, based on latest `main`.

## Background

Task-06 Desktop Mock AI E2E Smoke Verification 中发现了一个预先存在的 ORM/DDL 不匹配问题：

| 层级 | 当前状态 | 说明 |
|------|---------|------|
| DDL (`migrations/ddl/001–008.sql`) | `TIMESTAMPTZ` | PostgreSQL 推荐类型，存储 UTC |
| SQLAlchemy models (`app/models/*.py`) | `Mapped[datetime]` 无 `timezone=True` | 映射到 `TIMESTAMP WITHOUT TIME ZONE` |
| Python 默认值 | `datetime.now(timezone.utc)` | 生成 timezone-aware 对象 |
| PostgreSQL server_default | `func.now()` | 在 PG 中返回 `TIMESTAMPTZ` |

**三个层面方向一致（都指向 UTC），但 ORM 声明类型缺失 `timezone=True`，导致 SQLAlchemy 与 PostgreSQL DDL 创建的表结构不匹配。**

具体症状：
1. DDL 创建 `TIMESTAMPTZ` 列，但 ORM 的 `DateTime`（无 timezone）期望 `TIMESTAMP WITHOUT TIME ZONE`
2. asyncpg 在读写时因为类型声明不匹配而报错
3. `Base.metadata.create_all()` 对 PostgreSQL 创建 `TIMESTAMP WITHOUT TIME ZONE`，与 DDL 不一致
4. SQLite 不区分时区类型，所以 147 个现有测试和 Task-06 smoke 都正常工作

影响范围：
- 本地开发无法使用 PostgreSQL（必须用 SQLite 绕过）
- CI `pg-integration` workflow 只测 DDL 执行，不测 ORM 读写
- 生产环境上线前必须修复，否则无法切换到 PostgreSQL

## Goal

统一 SQLAlchemy models 的 `DateTime` 列声明，使其与 DDL 的 `TIMESTAMPTZ` 对齐。

## Modification Reason

1. DDL 使用 `TIMESTAMPTZ` 是 PostgreSQL 最佳实践，设计意图正确
2. Python 代码已生成 timezone-aware datetime，只差 ORM 声明层面
3. 修复 ORM 声明比改 DDL 影响更小、更符合现有设计方向
4. 是后续所有 PostgreSQL 相关开发和测试的前置条件

## What To Build

### Core Fix: Add `DateTime(timezone=True)` to All DateTime Columns

对所有 `Mapped[datetime]` / `mapped_column()` 的 `DateTime` 列添加 `timezone=True`：

```python
# 修改前
created_at: Mapped[datetime] = mapped_column(
    default=lambda: datetime.now(timezone.utc),
    server_default=func.now(),
)

# 修改后
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    server_default=func.now(),
)
```

### 涉及模型和列（8 files, 18 columns）

| 模型文件 | 涉及列 |
|---------|--------|
| `app/models/user.py` | `created_at`, `updated_at` |
| `app/models/device.py` | `first_seen_at`, `last_seen_at`, `created_at`, `updated_at` |
| `app/models/auth_session.py` | `expires_at`, `revoked_at`, `created_at`, `updated_at` |
| `app/models/credit_account.py` | `period_start`, `period_end`, `created_at`, `updated_at` |
| `app/models/credit_ledger.py` | `created_at` |
| `app/models/provider_call_log.py` | `created_at` |
| `app/models/risk_log.py` | `created_at` |
| `app/models/usage_event.py` | `created_at` |

### 辅助修改（使用现有文件，不新增文件）

1. **`cloud-backend/scripts/dev_seed_user.py`** — docstring 更新，移除已解决的 mismatch 警告
2. **文档更新**：
   - `docs/25-desktop-mock-e2e-smoke.md` — 移除 PG 绕过说明，新增 PG 可用路径
   - `docs/11-cloud-backend-guide.md` — PG 状态从 blocked 更新为 supported
   - `docs/12-database-design.md` — 添加 timestamp 对齐说明
   - `docs/sprint-02-summary.md` — Task-07 完成记录
   - `tasks/current-task.md` — 本文件
   - `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md` — 新建模块上下文

### DDL 文件 — 不修改

`migrations/ddl/*.sql` 文件不修改。`TIMESTAMPTZ` 是正确的选择，ORM 应该对齐 DDL，而非反向。

## What Not To Build

- 不修改 DDL 文件
- 不修改 API、services、core、providers、schemas 代码
- 不修改 shared、desktop-app、official-website
- 不修改 CI workflows、依赖文件、.env
- 不新增测试文件或验证脚本
- 不对 `app/services/` 和 `app/api/` 中的 datetime 使用做全量审计（超出范围）

## Allowed Files

- `cloud-backend/app/models/user.py`
- `cloud-backend/app/models/device.py`
- `cloud-backend/app/models/auth_session.py`
- `cloud-backend/app/models/credit_account.py`
- `cloud-backend/app/models/credit_ledger.py`
- `cloud-backend/app/models/provider_call_log.py`
- `cloud-backend/app/models/risk_log.py`
- `cloud-backend/app/models/usage_event.py`
- `cloud-backend/scripts/dev_seed_user.py`
- `docs/25-desktop-mock-e2e-smoke.md`
- `docs/11-cloud-backend-guide.md`
- `docs/12-database-design.md`
- `docs/sprint-02-summary.md`
- `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md`（新建）
- `tasks/current-task.md`

## Forbidden Files

- `cloud-backend/migrations/ddl/*.sql` — DDL 不修改
- `cloud-backend/migrations/migration-plan-draft.md`
- `cloud-backend/app/api/**` — API 代码不涉及
- `cloud-backend/app/services/**` — 服务代码不涉及
- `cloud-backend/app/core/**` — 核心代码不涉及
- `cloud-backend/app/providers/**` — Provider 代码不涉及
- `cloud-backend/app/schemas/**` — Schema 不涉及
- `cloud-backend/tests/**` — 测试文件不修改
- `shared/**` — 共享定义不涉及
- `desktop-app/**` — 桌面端不涉及
- `official-website/**` — 官网不涉及
- `.github/workflows/**` — CI 不涉及
- 依赖文件（`pyproject.toml`, `package.json`, lockfiles 等）
- `.env` 或 `.env.example`

> 注意：本次 forbidden 范围不同于 Task-06。Task-06 禁止整个 `cloud-backend/app/**`，本次允许修改 `cloud-backend/app/models/**` 下的 8 个模型文件，仅禁止 `app/api/`, `app/services/`, `app/core/`, `app/providers/`, `app/schemas/` 子目录。

## Acceptance Criteria

1. 所有 8 个模型文件的 18 个 DateTime 列均已添加 `DateTime(timezone=True)`
2. 现有 147 个 SQLite 测试全部通过（回归验证）
3. PostgreSQL DDL 集成测试全部通过（55 tests）
4. 使用现有 `dev_seed_user.py` 在 PostgreSQL 环境下运行成功，验证 ORM 对 PostgreSQL 读写正常。不新增测试文件或验证脚本
5. `git diff --check` 通过
6. 文档更新完成，移除 SQLite 绕过的已知问题记录

## Test Method

### 回归测试（必须通过）

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py
# 预计 147 passed
```

### PostgreSQL 集成测试（必须通过）

```bash
# 启动 PostgreSQL 容器
docker run -d --name pg-test-07 \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:16

until docker exec pg-test-07 pg_isready -U postgres; do sleep 1; done

# 运行集成测试
cd D:/Project/ad-assistant/cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  python -m pytest tests/test_migrations_integration.py -v

# 清理
docker rm -f pg-test-07
```

### PostgreSQL ORM 读写验证（使用现有文件，不新增文件）

方式一（用现有种子脚本）：
```bash
cd D:/Project/ad-assistant/cloud-backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  python -m pytest tests/test_migrations_integration.py -v

DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/postgres \
  JWT_SECRET_KEY="dev-secret-key" \
  python scripts/dev_seed_user.py
```

方式二（内联 Python 验证）：
```bash
cd D:/Project/ad-assistant/cloud-backend
DATABASE_URL="postgresql+asyncpg://postgres:test@localhost:5432/postgres" \
JWT_SECRET_KEY="dev-secret-key" \
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base
import app.models.user, app.models.device, app.models.auth_session
import app.models.risk_log, app.models.usage_event
import app.models.provider_call_log, app.models.credit_account, app.models.credit_ledger

async def verify():
    e = create_async_engine('postgresql+asyncpg://postgres:test@localhost:5432/postgres')
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('OK: ORM create_all against PostgreSQL succeeded')
    await e.dispose()
asyncio.run(verify())
"
```

> 以上两种方式均使用现有文件，不产生新文件。执行者任选其一验证即可。

## Risk Assessment

| 风险 | 等级 | 说明 |
|------|------|------|
| ORM 行为变更 | **中** | `DateTime(timezone=True)` 后，从 PG 读取的 datetime 对象始终带时区。现有业务代码如果对 datetime 做 naive 假设可能出问题 |
| SQLite 兼容性 | **低** | SQLite 不区分时区类型，行为与之前相同 |
| `datetime.utcnow()` 废弃 | **低** | Python 3.12 中已废弃，可在对齐时一并修复 |
| PostgreSQL CI 中断 | **低** | CI workflow 只测 DDL 执行，不测 ORM 读写 |

## Rollback Plan

1. 撤销所有模型文件中新增的 `DateTime(timezone=True)` → 恢复为 `Mapped[datetime]` 无 `timezone=True`
2. 还原文档中移除的 PostgreSQL 警告
3. 无需数据库回滚（DDL 未修改，且无生产数据）

回滚命令：
```bash
git revert <task-07-commit>
```

## Backward Compatibility

- **SQLite**：完全兼容。`DateTime(timezone=True)` 在 SQLite 中的行为与之前相同
- **PostgreSQL DDL**：修复后完全对齐，DDL 和 ORM 均使用 `TIMESTAMPTZ`
- **现有测试**：兼容。147 个 SQLite 测试预期全部通过
- **CI**：兼容。`pg-integration` workflow 预期通过

## Major Change Status

**是 — 重大变更。** 原因：修改数据库模型列类型声明属于 CODEX.md 中定义的重大变更（"修改数据库表结构"）。

**用户已于 2026-06-01 确认此重大变更。**

此变更是 **仅 ORM 声明对齐已有 DDL**，不改变：
- 数据库物理表结构（DDL 不变）
- API 契约
- 磁盘上的数据格式
- Provider 接口

属于重大变更清单中最轻量的一类。

## Dependency Permission

不允许新增依赖。仅修改已有文件。

## Security Requirements

- 不下发 API Key 到客户端
- 不由客户端扣点
- 不由客户端决定套餐
- 不绕过云端授权
- 不明文保存 Token
- AI 调用写入 provider_call_log（本次不涉及）

## Review Instructions For Codex

Review Sprint-02 Task-07 Backend PostgreSQL DateTime Alignment.

Focus on:

1. whether only model files + docs were changed
2. whether no DDL, API, service, provider, shared, desktop, or dependency changes were made
3. whether test results are complete (SQLite 147, PG 55, ORM read/write)
4. whether the change is within the user-confirmed major change scope
5. whether documentation updates correctly reflect the fix

Output:

- blocking issues
- high-risk issues
- medium/low-risk issues
- verification conclusion
- whether commit is allowed

## Completion Output Required

Implementer must report:

- changed files (with diff stat)
- exact test commands and results
- ORM PostgreSQL read/write verification results
- confirmation that no DDL, API, service, provider, shared, desktop, or dependency changes were made
- confirmation that no new test files or scripts were created
- residual risks
- module context updated
- wait for Codex Review, do not self-merge

---

## Implementation Record (2026-06-01)

### Changed Files (14 files, +95/−46)

**Models (core fix — 8 files):**

- `cloud-backend/app/models/user.py` — `DateTime(timezone=True)` ×2
- `cloud-backend/app/models/device.py` — `DateTime(timezone=True)` ×4
- `cloud-backend/app/models/auth_session.py` — `DateTime(timezone=True)` ×4
- `cloud-backend/app/models/credit_account.py` — `DateTime(timezone=True)` ×4
- `cloud-backend/app/models/credit_ledger.py` — `DateTime(timezone=True)` ×1
- `cloud-backend/app/models/provider_call_log.py` — `DateTime(timezone=True)` ×1
- `cloud-backend/app/models/risk_log.py` — `DateTime(timezone=True)` ×1
- `cloud-backend/app/models/usage_event.py` — `DateTime(timezone=True)` ×1

**Seed Script (1 file):**

- `cloud-backend/scripts/dev_seed_user.py` — docstring updated (mismatch resolved)

**Documentation (5 files):**

- `docs/25-desktop-mock-e2e-smoke.md` — removed PG bypass, added PG alternative section
- `docs/11-cloud-backend-guide.md` — updated PG status from blocked to supported
- `docs/12-database-design.md` — added timestamp alignment note
- `docs/sprint-02-summary.md` — added Task-07 status block
- `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md` — new module context

### Verification Results

| Test | Result |
|------|--------|
| SQLite regression (147 tests) | ✅ 147 passed |
| PG DDL integration (55 tests) | ✅ 55 passed |
| ORM `create_all` against PG | ✅ succeeded |
| `dev_seed_user.py` against PG | ✅ user created + device bound |
| `git diff --check` | ✅ passed |

### Confirmations

- ✅ Only allowed files modified
- ✅ DDL (`migrations/ddl/*.sql`) not modified
- ✅ API, services, core, providers, schemas not modified
- ✅ shared, desktop-app, official-website not modified
- ✅ CI workflows, dependency files, .env not modified
- ✅ No new test files or scripts created
- ✅ No secrets or provider keys added

### Not Implemented

- No full audit of datetime usage in `app/services/` and `app/api/` (out of allowed file scope; grep check found no obvious issues)
- No new automated test files added

### Residual Risks

- Services/api code may contain datetime naive assumptions — needs future targeted review
- Full backend integration smoke against PostgreSQL (start backend, login, mock AI call) was not repeated — covered by Task-06 runbook's PG alternative section

### Module Context

Updated: `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md`

### Next: Wait for Codex Review

Do NOT commit. Do NOT self-merge. Wait for Codex Review approval.

---

> **任务单创建日期**：2026-06-01
> **实施完成日期**：2026-06-01
> **参考**：`tasks/sprint-02-task-07-draft.md`, `docs/25-desktop-mock-e2e-smoke.md`, `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md`
