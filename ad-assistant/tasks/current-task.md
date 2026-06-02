# S05-R04: 月度积分发放调度器

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-04-monthly-credit-grant`

## 完成摘要

- `monthly_grant_service.py`（NEW）：幂等检查 + 单用户发放 + 批量编排，幂等键 `source_type="system"` + `source_id="{user_id}:{YYYY-MM}"`
- `scripts/run_monthly_grant.py`（NEW）：CLI 脚本，支持 `--year`/`--month`/`--dry-run`
- `POST /api/v1/admin/monthly-grant/run`：管理员手动触发端点（需 `credits:grant` 权限）
- `MonthlyGrantRequest` + `MonthlyGrantResponse` schema
- 复用 `grant_credits()`（`source_type="system"`），不修改 credit_service 或 models
- 16 tests：幂等性、跨月、跳过规则、dry-run、admin 权限隔离
- 全量测试：332 passed, 74 skipped
- 未实现：cron 部署、自动重试、大批量分批

## 背景

S04-T04 完成套餐和充值的最小商业链路：[plan.py](ad-assistant/cloud-backend/app/models/plan.py) 的 `monthly_credits` 字段已定义各套餐月度赠送额度（standard/expert/enterprise）。[credit_service.py](ad-assistant/cloud-backend/app/services/credit_service.py) 的 `grant_credits()` 已支持 `source_type="system"` 的积分授予操作。[CreditLedger](ad-assistant/cloud-backend/app/models/credit_ledger.py) 有 `source_type` 和 `source_id` 字段可承载幂等键。

但套餐月度赠送积分尚未自动发放。当前购买后积分一次性到账（通过 `recharge_service`），后续月份需要单独的调度器来定期发放。

## 用户目标

让套餐用户按月获得约定积分额度（`plan.monthly_credits`），并保证发放记录可追踪、可幂等、可回滚、可通过管理员手动触发。

## What To Build

### 1. 月度发放服务（NEW: `monthly_grant_service.py`）

- 函数 `process_monthly_grants(db, year, month)` — 主编排器
- 函数 `grant_monthly_credits_for_user(db, user, year, month)` — 单用户发放
- **幂等键设计**：`source_type = "monthly_grant"`，`source_id = f"{user_id}:{year}-{month:02d}"`
- 发放前检查 `credit_ledger` 是否已存在相同 `source_type` + `source_id` + `user_id` 记录
- 查询逻辑：
  - 找出 `users.status = "active"` 且 `credit_accounts.status = "active"` 且 `plans.monthly_credits > 0` 的用户
  - 跳过已发放当月积分的用户
- 发放时调用已有的 `grant_credits(db, user_id, amount, source_type="monthly_grant", source_id=..., description=...)`
- 返回汇总：`{granted: int, skipped: int, failed: int, errors: list[dict]}`

### 2. CLI 脚本（NEW: `scripts/run_monthly_grant.py`）

- 用法：`python scripts/run_monthly_grant.py [--year YYYY] [--month MM] [--dry-run]`
- 默认发放当前月份
- `--dry-run` 模式：只统计哪些用户将被发放，不实际执行
- 输出发放汇总到 stdout

### 3. Admin 手动触发端点（修改 `admin.py`）

- 新增 `POST /api/v1/admin/monthly-grant/run`
- 权限：`credits:grant`（与积分授权一致）
- 请求体可选：`{year: int, month: int}`，默认当前月份
- 返回发放汇总

### 4. Schema（修改 `admin.py` schemas）

- 新增 `MonthlyGrantRequest`：`year: int | None`, `month: int | None`
- 新增 `MonthlyGrantResponse`：`granted: int`, `skipped: int`, `failed: int`, `errors: list`

### 5. 测试（NEW: `tests/test_monthly_grant.py`）

- 幂等性：同一用户同一月不会重复发放
- 余额验证：发放后 balance 正确增加
- 跨月验证：同一用户可以收到不同月份的发放
- 跳过规则：无 monthly_credits 的用户被跳过
- 跳过规则：inactive 用户被跳过
- 错误路径：grant_credits 失败时记录错误但不中断其他用户
- 空数据集：无符合条件的用户时返回空汇总

### 6. 文档

- 新增 `docs/module-context/sprint-05-risk-04-monthly-credit-grant/context.md`
- 更新 `docs/07-ai-cost-control.md`（如需要）

### 7. 进度记录

- 追加更新 `PROGRESS.md`

## What Not To Build

- 不接入真实支付
- 不做复杂订阅续费（自动续费、过期宽限期等）
- 不做 cron 部署或 CI 调度配置（仅提供脚本，调度由运维自行配置）
- 不修改 `recharge_service` 或充值流程
- 不在桌面端添加月度发放 UI
- 不新增依赖（包括 APScheduler、Celery 等调度框架）

## Allowed Files

- `cloud-backend/app/services/monthly_grant_service.py`（NEW）
- `cloud-backend/scripts/run_monthly_grant.py`（NEW）
- `cloud-backend/app/api/v1/admin.py`
- `cloud-backend/app/schemas/admin.py`
- `cloud-backend/tests/test_monthly_grant.py`（NEW）
- `docs/07-ai-cost-control.md`
- `docs/module-context/sprint-05-risk-04-monthly-credit-grant/context.md`（NEW）
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- 真实支付接口
- CI/deployment cron 配置
- desktop UI
- Provider 路由
- Tauri permissions
- `cloud-backend/app/models/**`（无新模型，复用现有 credit_ledger）
- `cloud-backend/app/core/config.py`（不需新配置）
- `cloud-backend/app/services/credit_service.py`（复用，不修改）

## Acceptance Criteria

- [ ] 同一用户同一月份不会重复发放（幂等）
- [ ] 发放写入 `credit_ledger`（source_type="monthly_grant"，source_id 包含年月）
- [ ] 失败用户记录错误但不中断其他用户的发放
- [ ] 余额正确增加（通过已有的 `grant_credits` 原子更新）
- [ ] `--dry-run` 模式只统计不执行
- [ ] Admin 端点可手动触发发放
- [ ] 测试覆盖：幂等性、跨月、跳过规则、错误路径
- [ ] `python -m pytest tests/ -v` 通过（所有已有测试 + 新增）
- [ ] `git diff --check` 通过

## Test Method

必须运行：

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/ -v
```

```powershell
git diff --check
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 credit ledger 写入和积分发放逻辑，直接影响用户余额。

必须暂停确认的情况：
- 需要修改 `credit_service.py` 核心逻辑
- 需要修改数据库 DDL 或模型
- 需要新增第三方依赖
- 测试失败无法在任务范围内修复

## Security Requirements

- 只能服务端发放积分，客户端不可触发
- 发放必须写入 ledger，可审计
- Admin 手动触发端点受 `PermissionChecker("credits:grant")` 保护
- 不允许客户端决定发放额度（额度来自 `plan.monthly_credits`）
- `--dry-run` 不修改任何数据

## Rollback Plan

1. Revert 本任务 commit
2. 已发放的积分通过 `credit_ledger` 反向记录（冲正），不直接修改 balance
3. 移除 admin 触发端点
4. 不影响用户数据、订单或 Provider

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 幂等方案说明
- 发放规则说明
- 测试命令和结果
- 未实现内容
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
