# S05-R06: 模拟充值风控与订单状态加固

## 状态

`IN_PROGRESS`

## 分支

`feature/sprint-05-risk-06-recharge-risk-control`

## 背景

当前充值是 simulated 即时到账（`ENABLE_SIMULATED_PAYMENT=True` 时），适合 MVP 演示，但缺少防重复提交、订单状态机、金额校验和频率限制。真实支付前应先把订单状态和风控基础打牢。

S04-T04 已实现 `RechargeOrder` 模型和 `create_recharge_order()`，但：
- 订单状态仅有 `pending` / `completed`，无显式状态机守卫
- 无幂等键，重复提交会创建多个订单
- 无充值金额上下限校验（只校验了 `> 0`）
- 无频率限制

## 用户目标

在不接入真实支付的前提下，提升模拟充值的安全边界：订单状态清晰、重复提交可控、异常金额/频率可拦截。

## What To Build

### 1. 订单状态机（`recharge_service.py`）

定义状态常量与合法转移：

```
PENDING → COMPLETED  (simulated payment 成功)
PENDING → FAILED     (处理异常)
```

- 不允许从 `completed` / `failed` 回退
- `complete_order(db, order_id)` / `fail_order(db, order_id)` 守卫函数
- `RechargeOrder.status` 使用 module-level 常量而非裸字符串

### 2. 幂等键防重复提交

- `RechargeOrder` 模型新增 `idempotency_key: str | None` 列（String(64)）
- `RechargeRequest` schema 新增 `idempotency_key: str | None`
- 创建订单前查询：同一 user 下相同 idempotency_key 的已有订单
  - 已完成 → 返回已有订单结果（幂等返回）
  - 待处理 → 409 Conflict
  - 不存在 → 正常创建
- idempotency_key 为 None 时跳过幂等检查

### 3. 充值金额校验

- 最小金额：1 CNY（已有 `> 0` 检查，补充明确常量）
- 最大金额：`MAX_RECHARGE_AMOUNT_CNY`（默认 99999 CNY，可配置）
- `settings` 新增配置项

### 4. 频率限制

- 同一用户 N 秒内最多 M 笔充值请求
- 配置：`RECHARGE_RATE_LIMIT_COUNT`（默认 10）、`RECHARGE_RATE_LIMIT_WINDOW_SECONDS`（默认 3600）
- 统计近期订单数基于 `RechargeOrder.created_at`
- 超限返回 429 Too Many Requests

### 5. 数据库迁移

- `migrations/002_add_recharge_risk_control.sql`：添加 `idempotency_key` 列
- `migrations/002_rollback.sql`：回滚 SQL

### 6. 测试（`test_recharge.py` 扩展）

- 幂等：相同 key 返回已有订单、重复 pending 返回 409、无 key 正常
- 金额：小于最小值拒绝、超过最大值拒绝、合法金额通过
- 频率：超限拒绝、窗口外允许
- 状态机：complete 后不可再 complete、failed 后不可 complete
- API 集成：幂等返回、429 响应

### 7. 文档

- 新增 `docs/module-context/sprint-05-risk-06-recharge-risk-control/context.md`
- 更新 `PROGRESS.md`

## What Not To Build

- 不接入微信支付/支付宝
- 不处理真实回调验签
- 不做退款 / 取消订单 API
- 不做完整反欺诈系统
- 不修改 `credit_service.py`
- 不做 IP 级别风控

## Allowed Files

- `cloud-backend/app/models/recharge_order.py`
- `cloud-backend/app/services/recharge_service.py`
- `cloud-backend/app/api/v1/credits.py`
- `cloud-backend/app/schemas/recharge.py`
- `cloud-backend/app/core/config.py`
- `cloud-backend/migrations/002_add_recharge_risk_control.sql`（NEW）
- `cloud-backend/migrations/002_rollback.sql`（NEW）
- `cloud-backend/tests/test_recharge.py`
- `docs/19-pricing-and-credit-system.md`
- `docs/module-context/sprint-05-risk-06-recharge-risk-control/context.md`（NEW）
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- 真实支付 SDK / Provider
- desktop UI
- Tauri permissions
- CI/deployment
- `credit_service.py`

## Acceptance Criteria

- [ ] 重复充值请求不会重复入账（幂等键）
- [ ] 异常金额（≤0 或 >MAX）被拒绝
- [ ] 高频请求被拒绝（429）
- [ ] 订单状态变更受状态机守卫
- [ ] 测试覆盖：幂等、异常金额、高频、状态机、正常成功路径
- [ ] `python -m pytest tests/test_recharge.py -v` 通过
- [ ] `python -m pytest tests/ -v` 通过
- [ ] `git diff --check` 通过

## Test Method

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/test_recharge.py -v
python -m pytest tests/ -v
```

```powershell
git diff --check
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及充值、积分和风控逻辑，以及数据库 schema 变更（新增 idempotency_key 列）。

必须暂停确认的情况：
- 需要接入真实支付 SDK
- 需要修改 credit_service.py 或 credit_ledger 结构
- 需要新增第三方依赖

## Security Requirements

- 积分只能由服务端授予
- 不信任客户端金额、套餐或订单状态
- 不写入真实支付凭据
- 幂等键不暴露其他用户订单信息

## Rollback Plan

- revert 本任务 commit
- 运行 `migrations/002_rollback.sql` 删除 idempotency_key 列
- 如已产生测试数据，通过 ledger 反向记录纠正

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 状态机说明
- 风控规则说明
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
