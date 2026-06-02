# S05-R06: 模拟充值风控与订单状态加固

## 背景

S04-T04 已实现 `RechargeOrder` 模型和 `create_recharge_order()`，但缺少防重复提交、订单状态机、金额校验和频率限制。真实支付前需先把订单状态和风控基础打牢。

S05-R06 实现充值订单状态机、幂等键、金额校验和频率限制。

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/models/recharge_order.py` | 新增 `ORDER_STATUS_PENDING/COMPLETED/FAILED` 常量、状态转移表、`idempotency_key` 列、`failed_at` 列 |
| `app/services/recharge_service.py` | 新增异常类（`RechargeRiskError` 及其子类）、状态机守卫（`_complete_order`/`_fail_order`）、风控校验函数（`_validate_amount`/`_check_rate_limit`/`_resolve_idempotency`）、重构 `create_recharge_order` |
| `app/api/v1/credits.py` | 处理新异常类型：409 DUPLICATE_ORDER、400 INVALID_AMOUNT、429 RATE_LIMITED |
| `app/schemas/recharge.py` | `RechargeRequest` 新增 `idempotency_key`；`RechargeResponse` 新增 `idempotent_replay` |
| `app/core/config.py` | 新增 `MAX_RECHARGE_AMOUNT_CNY`、`MIN_RECHARGE_AMOUNT_CNY`、`RECHARGE_RATE_LIMIT_COUNT`、`RECHARGE_RATE_LIMIT_WINDOW_SECONDS` |
| `tests/test_recharge.py` | 新增 30 tests：金额校验（6）、频率限制（4）、幂等（7）、状态机（9）、API 集成（4） |
| `migrations/002_add_recharge_risk_control.sql` | **NEW** — 添加 `idempotency_key`、`failed_at` 列 + 唯一索引 |
| `migrations/002_rollback.sql` | **NEW** — 回滚 |

## 订单状态机

```
PENDING ──▶ COMPLETED   (simulated payment 成功，积分已发放)
PENDING ──▶ FAILED      (处理异常)
```

- COMPLETED → 任何状态：拒绝
- FAILED → 任何状态：拒绝
- 状态常量：`ORDER_STATUS_PENDING` / `ORDER_STATUS_COMPLETED` / `ORDER_STATUS_FAILED`
- 守卫函数：`_validate_transition(from, to)`
- 转换函数：`_complete_order(db, order)` / `_fail_order(db, order)`

## 风控规则

### 幂等键

| 场景 | 行为 |
|------|------|
| 无 idempotency_key | 跳过幂等检查（向后兼容） |
| 相同 key + COMPLETED 订单 | 200 返回已有订单（idempotent_replay=True），不重复入账 |
| 相同 key + PENDING 订单 | 409 DUPLICATE_ORDER |
| 相同 key + FAILED 订单 | 409 DUPLICATE_ORDER（提示换新 key） |
| 不同用户 + 相同 key | 允许（各自独立） |

### 金额校验

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MIN_RECHARGE_AMOUNT_CNY` | 1 | 单笔最小充值（CNY） |
| `MAX_RECHARGE_AMOUNT_CNY` | 99999 | 单笔最大充值（CNY） |

### 频率限制

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RECHARGE_RATE_LIMIT_COUNT` | 10 | 窗口内最大订单数 |
| `RECHARGE_RATE_LIMIT_WINDOW_SECONDS` | 3600 | 滑动窗口（秒） |

统计基于 `RechargeOrder.created_at`，按用户隔离。

## 安全

- 积分只能由服务端授予
- 不信任客户端金额、套餐或订单状态
- 不写入真实支付凭据
- 幂等键不暴露其他用户订单信息

## 测试

```bash
python -m pytest tests/test_recharge.py -v  # 54 passed
python -m pytest tests/ -v                   # 380 passed, 74 skipped
```

## 残余风险

- 幂等键唯一约束在 migration 中用 partial index 实现（WHERE idempotency_key IS NOT NULL AND status <> 'failed'），需 PostgreSQL 9.5+
- 频率限制基于 created_at 而非物理时间戳，理论上可通过系统时钟回拨绕过（风险极低）
- 未实现 IP 级别风控
- 未实现取消订单 API（PENDING → CANCELLED）
- 未实现退款流程
