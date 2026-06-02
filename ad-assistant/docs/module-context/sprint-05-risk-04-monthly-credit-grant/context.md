# S05-R04: 月度积分发放调度器

## 背景

Plan 模型已有 `monthly_credits` 字段定义套餐月度赠送额度。`grant_credits()` 支持 `source_type="system"` 的积分授予。但月度积分发放无自动化机制——购买套餐后仅一次性到账，后续月份需手动操作。

S05-R04 实现月度积分发放调度器的核心服务逻辑、CLI 脚本和管理手动触发端点。

## 变更范围

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/services/monthly_grant_service.py` | 月度发放服务：幂等检查 + 单用户发放 + 批量编排 |
| `scripts/run_monthly_grant.py` | CLI 脚本：`--year` / `--month` / `--dry-run` |
| `tests/test_monthly_grant.py` | 16 tests：幂等性、跨月、跳过规则、dry-run、admin 端点权限 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/api/v1/admin.py` | 新增 `POST /monthly-grant/run` 端点 |
| `app/schemas/admin.py` | 新增 `MonthlyGrantRequest` + `MonthlyGrantResponse` |

### 未修改

- `credit_service.py` — 复用 `grant_credits()`，不修改
- `models/` — 无新模型
- `config.py` — 不需新配置
- 桌面端 — 不涉及

## 幂等方案

**幂等键**: `source_type="system"` + `source_id="{user_id}:{YYYY-MM}"`

发放前查询 `credit_ledger` 是否已存在相同 (user_id, source_type, source_id) 记录：
- 存在 → 跳过
- 不存在 → 调用 `grant_credits()` 发放

发放失败的用户记录错误但不中断其他用户的发放。

## 发放规则

1. 查询 `users.status = "active"` AND `credit_accounts.status = "active"` AND `plans.monthly_credits > 0` 的用户
2. 按 `plan.monthly_credits` 额度发放
3. 跳过已发放当月的用户
4. 失败用户记录到 `errors` 列表

## 触发方式

| 方式 | 说明 |
|------|------|
| CLI 脚本 | `python scripts/run_monthly_grant.py [--year YYYY] [--month MM] [--dry-run]` |
| Admin API | `POST /api/v1/admin/monthly-grant/run`（需 `credits:grant` 权限） |

## 安全

- Admin 端点受 `PermissionChecker("credits:grant")` 保护
- CLI 脚本只在服务端执行
- 额度来自 `plan.monthly_credits`，客户端不可控制
- 所有发放写入 `credit_ledger`，可审计

## 测试

```bash
python -m pytest tests/test_monthly_grant.py -v  # 16 passed
python -m pytest tests/ -v                         # 332 passed, 74 skipped
```

## 残余风险

- 没有 cron/调度器部署（运维自行配置 Windows Task Scheduler 或 cron）
- 大量用户时一次发放可能超时（MVP 阶段用户量少，可后续加并发/分批）
- 没有发放失败重试机制（可手动重新运行脚本）
- 跨年跨月边界依赖服务器时钟
