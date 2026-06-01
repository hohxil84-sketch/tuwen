# Current Task: S04-T01 — Provider 可靠性：预扣检查 + 降级/重试

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED` — 已提交 PR #37，等待 Codex/用户复核。

## 背景

Sprint-03 已将首个真实 AI Provider（DeepSeek）接入生产路由并接通真实积分扣费，但存在两个已知安全/可靠性缺口（见 `docs/sprint-03-summary.md` § Residual Risks）：

1. **余额不足无拦截**：用户余额为 0 时 Provider 调用仍成功但不扣费（`credits_charged=0`），相当于免费调用。
2. **DeepSeek 无降级**：DeepSeek 不可用时（超时、鉴权失败、限流等）调用直接失败，无 fallback 到 mock。

本任务补齐这两个缺口，使 Provider 调用链路在计费和可用性两方面达到基本生产级。

## 本次只开发什么

### Part A: 预扣检查（Pre-flight Balance Check）

两级余额门禁——先看绝对最低余额，再看 feature 最低消耗：

**第一级：绝对最低余额**
- 新增配置项 `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL`（默认 1）。
- 若 `user_id` 不为 None 且余额 < 该值，直接拒绝。

**第二级：Feature 最低消耗预估（核心商业逻辑）**
- 新增配置项 `FEATURE_MIN_CREDITS`：`dict[str, int]`，按 feature 定义最低所需积分。
- 默认值（基于当前各 feature 最低调用成本）：
  - `mock_ad_copy`：2（MockProvider 默认用量约 0.01455 CNY → 2 积分；DeepSeek 少量 token 也在 1-2 积分）
  - `ocr`：1
  - `text_gen`：2
  - `image_edit`：5
- 预扣逻辑：`required = max(MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL, FEATURE_MIN_CREDITS.get(feature, 1))`，余额 < required → 拒绝。
- 原则：**不能亏** — 余额不足以覆盖 feature 最低消耗时，绝不调用 Provider。

**统一行为**
- 拒绝时：抛出专用异常 → `provider_call_log`（status=error, error_code=`INSUFFICIENT_BALANCE`）+ 不回退不重试。
- `user_id=None`（系统/内部调用）时跳过全部余额检查。
- API 层返回 402 Payment Required + 中文提示（含所需积分数和当前余额）。
- 在 `execute_provider_call()` 调用 Provider **之前**执行检查。

### Part B: Provider 降级 + 重试

- **降级（Fallback）**：当 primary provider 失败时，自动尝试 fallback provider。
  - 默认规则：`deepseek` → fallback `mock`（仅对 `mock_ad_copy/standard` 路由）。
  - Fallback 发生时记录降级事件到 `provider_call_log`（新增 `fallback_from` 字段或日志标记）。
  - 在 `route_and_execute_provider_call()` 中实现降级链。
- **重试（Retry）**：对超时/连接类瞬时错误，自动重试同一 provider 最多 2 次。
  - 重试间隔：指数退避（第 1 次重试等 1s，第 2 次等 2s）。
  - 重试适用于：`TIMEOUT`、`CONNECTION_ERROR`、`API_ERROR`（5xx）。
  - 不重试：`AUTH_ERROR`、`BAD_REQUEST`、`RATE_LIMITED`（限流应等待而非立即重试）。
- **路由器增强**：`ProviderRouter` 新增 `resolve_name(feature, plan) → str` 方法，返回 provider 名称而非实例，便于降级链逻辑按名查找 fallback。

### Part C: 错误响应增强

- `INSUFFICIENT_BALANCE` 错误在 API 返回中应包含 `error_code` 和用户可读的中文提示。
- 降级/重试后的最终失败，返回对用户友好的错误信息（而非原始异常堆栈）。

## 本次不开发什么

- 不开发熔断器（Circuit Breaker）或健康检查端点（Health Check API）。
- 不开发 DB 动态路由配置（路由规则仍为 Python dict）。
- 不开发多级降级链（deepseek → fallback1 → fallback2 → ...），只做一级降级。
- 不修改 `mock_ad_copy` 以外的 feature 路由规则。
- 不做动态 token 预估（无法在调用前精确预测 token 消耗），使用 feature 级最低积分阈值作为近似商业保护。不为此新增数据库表或外部定价服务。
- 不修改桌面端、Tauri、package.json、pyproject.toml 依赖。
- 不修改数据库 schema / DDL / migration。
- 不修改 API contract / shared DTO / OpenAPI spec（`credits_charged` 字段已存在，错误码为已有模式）。

## 允许修改哪些文件

- `cloud-backend/app/services/provider_service.py` — 预扣检查 + 重试逻辑
- `cloud-backend/app/providers/router.py` — `resolve_name()` 方法 + fallback 规则
- `cloud-backend/app/core/config.py` — `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL` 配置项
- `cloud-backend/app/api/v1/mock_ai.py` — INSUFFICIENT_BALANCE 错误处理
- `cloud-backend/tests/test_provider_reliability.py` (NEW) — 聚焦测试
- `cloud-backend/tests/test_provider_routing.py` — 更新路由相关测试（如有必要）
- `docs/07-ai-cost-control.md` — 预扣检查实现证据
- `docs/06-provider-architecture.md` — 降级/重试实现证据
- `tasks/current-task.md` — 实现记录
- `PROGRESS.md` — 进度记录

## 禁止修改哪些文件

- `cloud-backend/app/models/` — 不修改数据库模型
- `cloud-backend/app/providers/base.py` — ProviderResult / ProviderRequest 不修改
- `cloud-backend/app/providers/deepseek_provider.py` — 不修改
- `cloud-backend/app/providers/mock_provider.py` — 不修改
- `cloud-backend/app/services/credit_service.py` — 不修改（预扣检查由 provider_service 调用现有接口）
- `cloud-backend/app/services/cost_service.py` — 不修改
- `desktop-app/` — 全部禁止
- `shared/` — 全部禁止
- `cloud-backend/pyproject.toml` — 不新增依赖
- `cloud-backend/migrations/` — 不做数据库迁移

## 验收标准

### Part A
- [ ] `execute_provider_call` 在调用 Provider 前执行两级余额检查。
- [ ] 第一级：余额 < `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL`（默认 1）→ 拒绝。
- [ ] 第二级：余额 < `FEATURE_MIN_CREDITS.get(feature, 1)` → 拒绝（feature 最低消耗保护）。
- [ ] 拒绝时写入 `provider_call_log`（status=error, error_code=`INSUFFICIENT_BALANCE`），含当前余额和所需最低积分。
- [ ] `user_id=None`（系统/内部调用）时跳过全部余额检查，正常执行。
- [ ] `mock_ai.py` API 对 `INSUFFICIENT_BALANCE` 返回 402 Payment Required，含中文错误提示（所需积分 + 当前余额）。
- [ ] 配置项 `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL` 默认值为 1。
- [ ] 配置项 `FEATURE_MIN_CREDITS` 为 `dict[str, int]`，默认 `{"mock_ad_copy": 2, "ocr": 1, "text_gen": 2, "image_edit": 5}`。

### Part B
- [ ] DeepSeek 调用失败时，自动降级到 MockProvider（仅 `mock_ad_copy/standard` 路由）。
- [ ] 降级成功后返回 MockProvider 结果，`credits_charged` 按 mock 成本正常扣费。
- [ ] 降级发生时 `provider_call_log` 记录主 Provider 的 error 日志 + fallback Provider 的 success/error 日志。
- [ ] `TIMEOUT` / `CONNECTION_ERROR` / 5xx 类错误自动重试（最多 2 次，指数退避）。
- [ ] `AUTH_ERROR` / `BAD_REQUEST` / `RATE_LIMITED` 不重试，直接进入降级或失败。
- [ ] `ProviderRouter.resolve_name(feature, plan)` 方法可用，返回 provider 名字符串。
- [ ] 降级链全部失败时抛出最后一个错误，API 层返回友好错误。

### 通用
- [ ] 所有新功能有聚焦测试覆盖。
- [ ] 现有回归测试全部通过。
- [ ] `git diff --check` 通过。
- [ ] 不新增依赖。

## 测试方式

```bash
cd ad-assistant/cloud-backend

# 新聚焦测试
python -m pytest tests/test_provider_reliability.py -v -x

# 全量回归
python -m pytest tests/ -v --timeout=60 --ignore=tests/test_pg_integration.py
```

## 是否允许新增依赖

不允许。所有功能使用已有依赖（`openai` SDK for error types, `asyncio` for sleep, `sqlalchemy` for DB queries）。

## 是否涉及重大变更

**是** — 涉及以下高风险边界：

1. **Credit / Payment / 扣费**：新增预扣检查改变了 `execute_provider_call` 的执行流程，用户余额为 0 时不再允许调用。
   - **影响范围**：所有通过 `execute_provider_call` / `route_and_execute_provider_call` 的 API 端点（当前仅 `POST /api/v1/mock-ai/ad-copy`）。
   - **兼容性**：余额 > 0 的用户行为不变；余额 = 0 的用户从"成功但不扣费"变为"调用被拒绝"。
   - **回滚方案**：设置 `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL=0` 恢复旧行为，或 revert 对应提交。

2. **Provider 接口 / 模型路由**：新增降级链和重试改变了 provider 执行路径。
   - **影响范围**：`route_and_execute_provider_call` 的行为从"单次调用"变为"可能多次尝试"。
   - **兼容性**：primary provider 成功时行为完全不变；仅在 primary 失败时触发新逻辑。
   - **回滚方案**：移除 fallback 配置使降级链为空，或 revert 对应提交。

3. **修改原因**：这两个缺口是 Sprint-03 已识别的生产级安全隐患，补齐后才能安全地对真实用户开放 AI 调用。

### 不需要数据库迁移

所有改动在应用层（Python），不修改数据库 schema / DDL / migration。

## 安全检查

- [ ] 不下发 API Key 到客户端
- [ ] 不由客户端扣点
- [ ] 不由客户端决定套餐
- [ ] 不绕过云端授权
- [ ] 不明文保存 Token
- [ ] AI 调用写入 provider_call_log
- [ ] 预扣检查在云端执行，客户端不可绕过
- [ ] 降级链在云端执行，客户端不可选择 provider

## 风险点

1. **预扣检查两级门禁**：`FEATURE_MIN_CREDITS` 的默认值基于当前 mock 成本估算，未来新增 feature 或切换 provider 时可能需要调整。如果 feature 的实际成本因 prompt 长度波动超过最低阈值，部分调用仍可能出现"扣不够"（但现有 partial deduction 会扣到余额归零，不会透支）。DeepSeek 的最小 token 成本可能低于 mock，此时 mock 阈值作为安全上限。
2. **降级可能导致成本差异**：DeepSeek → mock 降级后，mock 的成本估算与 DeepSeek 实际成本不同，用户被扣的积分数不同。
3. **重试可能放大延迟**：最多 2 次重试 + 每次 1-2s 退避 → 最坏情况增加 ~3s 延迟。
4. **降级日志量**：每次 primary 失败 + 降级成功会产生 2 条 `provider_call_log`（error + success），需注意日志存储。

## 完成输出要求

- 修改文件列表
- 实现内容
- 未实现内容
- 自审结论
- 测试命令和结果
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
