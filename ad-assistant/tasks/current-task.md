# S05-R05: Provider 健康检查与熔断器

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-05-provider-health-circuit`

## 完成摘要

- `circuit_breaker.py`（NEW）：CLOSED → OPEN → HALF_OPEN 三态熔断器（阈值 3 次失败，冷却 60s）
- `route_and_execute_provider_call` 集成熔断器：调用前 CB 检查，成功/失败报告
- `GET /api/v1/admin/provider-health`：管理员/operator 查看所有 Provider 熔断状态
- `ProviderHealthItem` + `ProviderHealthResponse` schema
- 18 tests：状态机全生命周期（9）+ 注册表（5）+ admin 端点权限（3）+ 异常（1）
- 全量：350 passed, 74 skipped
- 未实现：DB 持久化、动态参数、HALF_OPEN 并发控制

## 背景

S04-T01 已实现 `FALLBACK_RULES` 降级链和 `_call_with_retry` 重试机制。当前 `route_and_execute_provider_call` 在 primary provider 失败后会尝试 fallback，但缺少熔断器（circuit breaker）——连续失败后仍会反复尝试同一个 Provider，浪费资源和用户等待时间。

Provider 故障时仍缺少：
- 熔断保护：连续失败后快速失败，不再尝试
- 冷却恢复：一段时间后允许半开探测
- 可观测性：管理员可查询各 Provider 健康状态

## 用户目标

在真实 Provider 不稳定时减少连续失败，提供最小健康状态和熔断保护，并允许管理员查看 Provider 状态。

## What To Build

### 1. 熔断器（NEW: `circuit_breaker.py`）

在 `app/providers/circuit_breaker.py` 中实现：

- `CircuitState` 枚举：`CLOSED`（正常）→ `OPEN`（熔断）→ `HALF_OPEN`（探测恢复）→ `CLOSED`
- `CircuitBreaker` 类：
  - 配置：`failure_threshold`（默认 3 次连续失败）、`cooldown_seconds`（默认 60s）
  - `before_call() -> bool`：调用前检查 — OPEN 且未冷却完成 → False；OPEN 且冷却完成 → 转 HALF_OPEN → True；CLOSED/HALF_OPEN → True
  - `on_success()`：成功 → 重置回 CLOSED
  - `on_failure()`：失败 → CLOSED/HALF_OPEN 下递增计数，达到阈值 → OPEN
  - `state` / `consecutive_failures` / `opened_at` 属性（用于健康检查展示）
- `CircuitBreakerRegistry`：`dict[provider_name, CircuitBreaker]` + 模块级单例
- `CircuitBreakerOpenError` 异常

### 2. 集成到 provider_service.py

修改 `route_and_execute_provider_call`：

- 在尝试每个 Provider 之前，检查其熔断器状态
- 熔断打开 → 记录日志 + 跳过该 Provider（若为 primary 则尝试 fallback；若 fallback 也熔断则抛出 `CircuitBreakerOpenError`）
- Provider 调用成功 → `cb.on_success()`
- Provider 调用失败（所有可捕获异常，除 `InsufficientBalanceError` 外）→ `cb.on_failure()`
- 熔断跳过时在 `provider_call_log` 中记录 `error_code="CIRCUIT_OPEN"`

### 3. 健康检查 Admin 端点

在 `admin.py` 中新增 `GET /api/v1/admin/provider-health`：

- 权限：`provider_logs:read`
- 返回每个已注册 Provider 的熔断器状态：
  ```json
  {
    "providers": {
      "deepseek": {"state": "CLOSED", "consecutive_failures": 0, "opened_at": null},
      "mock": {"state": "CLOSED", "consecutive_failures": 0, "opened_at": null}
    }
  }
  ```

### 4. Schema

在 `admin.py` schemas 中新增 `ProviderHealthItem` + `ProviderHealthResponse`。

### 5. 测试（NEW: `tests/test_circuit_breaker.py`）

- CLOSED → OPEN 转换：连续失败达到阈值后熔断
- OPEN 期间拒绝调用：`before_call()` 返回 False
- 冷却后转 HALF_OPEN：冷却时间到后允许一次探测
- HALF_OPEN 成功恢复：探测成功 → CLOSED
- HALF_OPEN 失败再熔断：探测失败 → 立即 OPEN
- 单次成功重置计数
- 模块级单例注册表
- Admin 端点返回 Provider 健康状态
- Provider 集成：连续失败后 primary 被熔断 → 走 fallback

### 6. 文档

- 新增 `docs/module-context/sprint-05-risk-05-provider-health-circuit/context.md`
- 更新 `docs/06-provider-architecture.md`（如需要）

### 7. 进度记录

- 追加更新 `PROGRESS.md`

## What Not To Build

- 不做复杂运维后台
- 不做数据库持久化熔断状态（内存即可，重启重置）
- 不做动态路由规则（规则已在 router.py）
- 不接入新 Provider
- 不修改价格模型或计费逻辑
- 不在桌面端展示 Provider 健康状态
- 不新增依赖（包括 resilience4j、pybreaker 等）

## Allowed Files

- `cloud-backend/app/providers/circuit_breaker.py`（NEW）
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/app/api/v1/admin.py`
- `cloud-backend/app/schemas/admin.py`
- `cloud-backend/tests/test_circuit_breaker.py`（NEW）
- `docs/06-provider-architecture.md`
- `docs/module-context/sprint-05-risk-05-provider-health-circuit/context.md`（NEW）
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- Payment/Credit 计费规则
- `credit_service.py`
- desktop UI
- Tauri permissions
- CI/deployment
- `app/models/**`（无新模型）
- `app/core/config.py`（熔断参数硬编码在 circuit_breaker.py 中）

## Acceptance Criteria

- [ ] 连续失败后 Provider 被短暂熔断（默认 3 次失败，60s 冷却）
- [ ] 熔断期间走 fallback 或返回明确 CIRCUIT_OPEN 错误
- [ ] 冷却后允许半开探测恢复
- [ ] 单次成功重置计数
- [ ] 管理员可通过 `GET /api/v1/admin/provider-health` 查看所有 Provider 熔断状态
- [ ] 测试覆盖：CLOSED→OPEN→HALF_OPEN→CLOSED 状态转换
- [ ] `python -m pytest tests/ -v` 通过
- [ ] `git diff --check` 通过

## Test Method

必须运行：

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/test_circuit_breaker.py -v
python -m pytest tests/ -v
```

```powershell
git diff --check
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 Provider 路由和调用可靠性，可能影响生产 AI 调用路径。

必须暂停确认的情况：
- 需要修改 Provider 接口（AsyncProvider base class）
- 需要修改 Payment/Credit 计费逻辑
- 需要新增第三方依赖

## Security Requirements

- 不泄露 API Key 或 raw provider payload
- 熔断状态不允许由客户端篡改（仅服务端内存）
- 健康检查端点受 `PermissionChecker("provider_logs:read")` 保护

## Rollback Plan

- revert 本任务 commit
- Provider 调用恢复现有 retry/fallback 行为（无熔断器）
- 熔断状态仅在内存，无数据库回滚需求

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 熔断规则说明
- 健康检查范围
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
