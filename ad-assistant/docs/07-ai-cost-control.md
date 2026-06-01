# 07 AI 成本控制

## 原则

不允许无限 AI 会员。
不允许固定写死所有功能点数。
不允许客户端扣点。

AI 成本必须按真实 Provider 成本或可追溯估算成本动态换算。

## 扣费链路

1. 用户发起 AI 功能。
2. 云端校验登录、设备、套餐、额度、风控状态。
3. 云端 Provider 层调用模型。
4. Provider 返回 usage、图片成本、GPU 时间或供应商成本。
5. 云端计算 `estimated_cost`。
6. 云端按汇率和倍率换算 `credits_charged`。
7. 云端扣除用户 AI 算力。
8. 云端写入 `provider_call_log`。
9. 云端返回结果和本次消耗。

## 成本字段

`estimated_cost`：
云端估算的人民币成本，必须可追溯。

`credits_charged`：
从用户 AI 算力额度扣除的数量。

`raw_usage`：
Provider 原始 usage，不直接暴露给普通客户端。

## 免费和本地功能

本地低成本功能可以不扣算力，但必须记录使用统计。

不扣算力的功能必须满足：
- 不调用云端付费 Provider
- 不消耗云端 GPU
- 不产生明显服务器成本

## 风控规则

必须支持：
- 用户级限流
- 设备级限流
- IP 级限流
- 异常失败率监控
- 高频调用监控
- 额度耗尽拦截
- 欠费拦截

## 后台报表

后台至少需要统计：
- 每日 Provider 成本
- 每日用户消耗
- 每功能成本
- 每模型成本
- 失败调用成本
- 用户毛利估算

## Sprint-02 Task-03: Mock Cost Estimate ✅ Implemented

Implemented on branch `feature/sprint-02-task-03-provider-mock`:

- mock-only cost estimation helper (`app/services/cost_service.py`);
- mock estimates are deterministic test values, not real provider pricing;
- estimates are nonnegative and traceable in tests;
- mock provider logs record `credits_charged=0`;
- mock provider calls do not write `credit_ledger`;
- real credit deduction and product pricing remain separate approved tasks.

## Sprint-02 Task-04: Mock AI API Endpoint ✅ Implemented

Implemented on branch `feature/sprint-02-task-04-mock-ai-api`:

- `POST /api/v1/mock-ai/ad-copy` — first authenticated, mock-only AI endpoint;
- endpoint logs provider calls with `credits_charged=0`;
- endpoint does not write `credit_ledger`;
- endpoint does not expose `raw_usage` or raw user text;
- mock cost values remain mock-only — not real billing.

## Sprint-03 Task-03: Real Credit Deduction ✅ Implemented

Implemented on branch `feature/sprint-03-task-03-credit-deduction`:

- added `CREDITS_PER_CNY: int = 100` to `Settings` (1 credit = ¥0.01);
- added `cny_to_credits()` in `cost_service.py` — converts CNY cost to integer credits with `ceil` rounding;
- added `deduct_credits()` in `credit_service.py` — atomically deducts from `CreditAccount.balance` and writes `credit_ledger`;
- wired deduction into `execute_provider_call()` — after successful provider call, cost is converted to credits and deducted;
- `credits_charged` in `provider_call_log` and API response now reflects actual deduction;
- partial deduction on insufficient balance (balance goes to 0, remaining cost is logged);
- `user_id=None` calls skip deduction (system/internal usage);
- 19 focused deduction tests + 211 total regression pass.

### CNY → credits conversion

```
credits = ceil(estimated_cost_cny × CREDITS_PER_CNY)
```

Default: `CREDITS_PER_CNY = 100` → 1 credit = ¥0.01. Always rounds UP (ceil) because the provider has already consumed resources.

### Deduction flow

```
execute_provider_call()
  → provider.call()          # AI call succeeds
  → cost_service             # Calculate CNY cost
  → cny_to_credits()         # Convert to credits
  → deduct_credits()         # Atomic: UPDATE balance, INSERT credit_ledger
  → record_provider_call()   # credits_charged = actual deduction
```

### What's not yet implemented

- Pre-flight balance check (block calls when balance is too low) — future task
- Plan-level cost multipliers — future task
- Monthly grant auto-replenish — future task
- Refund logic — future task

## Sprint-04 Task-01: Pre-flight Balance Check ✅ Implemented

Implemented on branch `feature/sprint-04-task-01-provider-reliability`:

- Added two-level pre-flight balance gate in ``execute_provider_call()`` (before provider invocation):
  - **Level 1 — absolute minimum**: ``MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL`` (default 1);
  - **Level 2 — feature minimum**: ``FEATURE_MIN_CREDITS`` dict per feature (e.g. ``mock_ad_copy``=2, ``image_edit``=5);
  - ``required = max(absolute_min, feature_min)`` → if ``balance < required`` → ``InsufficientBalanceError``.
- Blocked calls write ``provider_call_log`` with ``error_code="INSUFFICIENT_BALANCE"``, do NOT call provider, do NOT touch balance.
- ``user_id=None`` (system calls) skip balance check entirely.
- API layer (``mock_ai.py``) returns **402 Payment Required** with Chinese error message showing required vs current credits.
- Config: ``MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL=1``, ``FEATURE_MIN_CREDITS={"mock_ad_copy":2,"ocr":1,"text_gen":2,"image_edit":5}``.

### Pre-flight gate principle

**不能亏** — if the user's balance is below the feature's minimum expected cost, the provider is never called. This prevents the scenario where a provider consumes resources but the user only partially pays (or pays nothing).

### What's still not implemented

- Dynamic cost pre-estimation (token count prediction before calling) — the feature-level minimum is a conservative approximation.
- Fine-grained per-plan thresholds — all plans share the same ``FEATURE_MIN_CREDITS`` values.
