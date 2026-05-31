# Current Task: Backend timezone datetime model alignment

## Status

`IMPLEMENTED_AWAITING_CODEX_REVIEW`

Implementation completed on 2026-06-01 on branch `fix/backend-timezone-datetime`.

Base: `main` @ `8fa3440`.

## Suggested Branch

`fix/backend-timezone-datetime`, based on latest `main`.

## Background

`cloud-backend/app/models/*.py` 中有 8 个模型文件的 `Mapped[datetime]` 列使用了 SQLAlchemy 默认的 `DateTime`（无 timezone），但：

- DDL 声明的列类型是 `TIMESTAMPTZ`（带时区）
- Python 代码传入的是 timezone-aware datetime（`datetime.now(timezone.utc)`）
- asyncpg 拒绝将带时区的 datetime 写入无时区的 bind parameter

这导致所有涉及 datetime 列的写操作（login、device bind、provider log 等）在真实 PostgreSQL 上抛出 `DataError`。

## What To Build

### 唯一修复

在以下 8 个模型文件中，将 `Mapped[datetime]` 列对应的 `mapped_column()` 加上 `DateTime(timezone=True)`：

1. `cloud-backend/app/models/user.py`
2. `cloud-backend/app/models/device.py`
3. `cloud-backend/app/models/auth_session.py`
4. `cloud-backend/app/models/risk_log.py`
5. `cloud-backend/app/models/provider_call_log.py`
6. `cloud-backend/app/models/usage_event.py`
7. `cloud-backend/app/models/credit_account.py`
8. `cloud-backend/app/models/credit_ledger.py`

每个文件还需在 sqlalchemy import 中加上 `DateTime`。

## What Not To Build

- 不改 DDL
- 不改迁移
- 不改 API 路由 / schemas / deps
- 不改 auth / service 业务逻辑
- 不改 Provider / credit 逻辑
- 不改前端 / desktop-app
- 不改 shared / official-website
- 不改依赖

## Allowed Files

- `cloud-backend/app/models/user.py`
- `cloud-backend/app/models/device.py`
- `cloud-backend/app/models/auth_session.py`
- `cloud-backend/app/models/risk_log.py`
- `cloud-backend/app/models/provider_call_log.py`
- `cloud-backend/app/models/usage_event.py`
- `cloud-backend/app/models/credit_account.py`
- `cloud-backend/app/models/credit_ledger.py`
- `tasks/current-task.md`

## Forbidden Files

- `cloud-backend/migrations/**`
- `cloud-backend/app/api/**`
- `cloud-backend/app/schemas/**`
- `cloud-backend/app/services/**`
- `cloud-backend/app/providers/**`
- `cloud-backend/app/core/**`
- `desktop-app/**`
- `shared/**`
- `official-website/**`
- `.github/workflows/**`
- 依赖文件

## Acceptance Criteria

- 8 个模型文件的 `Mapped[datetime]` 列均添加 `DateTime(timezone=True)`
- auth login 在真实 PostgreSQL 上不再 500
- `python -m pytest tests/test_auth.py -v` 全部通过
- `python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py` 全部通过
- `git diff --check` 通过
- 未修改 DDL / 迁移 / API / auth / service / Provider / credit / 前端 / 依赖

## Test Method

```bash
cd D:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_auth.py -v
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py

cd D:/Project/ad-assistant
git diff --check
```

## Review Instructions For Codex

Review Backend timezone datetime model alignment.

Focus on:

1. 8 个模型文件是否全部覆盖
2. DateTime(timezone=True) 是否正确放置
3. 是否未修改 DDL / 迁移 / API / auth / service / Provider / credit
4. 是否未修改前端 / 依赖
5. 测试结果

Output:

- 覆盖完整性检查
- 边界检查
- 是否允许提交

## Implementation Evidence (2026-06-01)

### Changed Files

| Type | File | datetime 字段 |
|------|------|--------------|
| ✏ Modified | `cloud-backend/app/models/user.py` | `created_at`, `updated_at` |
| ✏ Modified | `cloud-backend/app/models/device.py` | `first_seen_at`, `last_seen_at`, `created_at`, `updated_at` |
| ✏ Modified | `cloud-backend/app/models/auth_session.py` | `expires_at`, `revoked_at`, `created_at`, `updated_at` |
| ✏ Modified | `cloud-backend/app/models/risk_log.py` | `created_at` |
| ✏ Modified | `cloud-backend/app/models/provider_call_log.py` | `created_at` |
| ✏ Modified | `cloud-backend/app/models/usage_event.py` | `created_at` |
| ✏ Modified | `cloud-backend/app/models/credit_account.py` | `period_start`, `period_end`, `created_at`, `updated_at` |
| ✏ Modified | `cloud-backend/app/models/credit_ledger.py` | `created_at` |

共 18 个 datetime 列，8 个文件。

### 变更内容

每条变更仅两件事：
1. sqlalchemy import 加 `DateTime`
2. `mapped_column()` 第一个参数加 `DateTime(timezone=True)`

### Test Results

```
python -m pytest tests/test_auth.py -v                                                    → 14 passed ✅
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py                  → 147 passed ✅
```

### Git Check

```
git diff --check → ✅ (no output)
```

### Boundary Confirmation

| 检查项 | 状态 |
|--------|------|
| 仅修改 8 个 model 文件 | ✅ |
| 仅加 DateTime(timezone=True) | ✅ |
| 未改 DDL | ✅ |
| 未改迁移 | ✅ |
| 未改 API / schemas / deps | ✅ |
| 未改 auth / service 逻辑 | ✅ |
| 未改 Provider / credit 逻辑 | ✅ |
| 未改前端 / desktop-app | ✅ |
| 未改依赖 | ✅ |

### Residual Risks

- 预存在的 SQLite 测试（使用无时区 DateTime）不受影响，因为 DateTime(timezone=True) 在 SQLite 上行为等价
- 此修复仅解决 Python↔PostgreSQL 时区类型不匹配，不改变任何业务行为
