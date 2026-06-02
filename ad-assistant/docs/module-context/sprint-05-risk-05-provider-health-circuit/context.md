# S05-R05: Provider 健康检查与熔断器

## 背景

S04-T01 已实现降级链（`FALLBACK_RULES`）和重试机制（`_call_with_retry`）。但缺少熔断器——Provider 连续失败后仍反复尝试，浪费资源和用户等待时间。

S05-R05 实现内存熔断器（circuit breaker），对每个 Provider 独立跟踪故障计数，连续失败后短暂熔断，冷却后允许半开探测恢复。

## 变更范围

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/providers/circuit_breaker.py` | 熔断器核心：CircuitBreaker + CircuitBreakerRegistry + CircuitBreakerOpenError |
| `tests/test_circuit_breaker.py` | 18 tests：状态机、注册表、admin 端点 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/services/provider_service.py` | `route_and_execute_provider_call` 集成熔断器检查/报告 |
| `app/api/v1/admin.py` | 新增 `GET /provider-health` 端点 |
| `app/schemas/admin.py` | 新增 `ProviderHealthItem` + `ProviderHealthResponse` |

## 熔断规则

### 状态机

```
CLOSED ──(连续失败≥3)──> OPEN ──(冷却60s)──> HALF_OPEN
  ^                                              │
  └──────────(成功)──────────────────────────────┘
                    HALF_OPEN ──(失败)──> OPEN
```

### 配置

| 参数 | 默认 | 说明 |
|------|------|------|
| `failure_threshold` | 3 | 连续失败次数阈值 |
| `cooldown_seconds` | 60 | 熔断冷却时间 |

### 集成点

在 `route_and_execute_provider_call` 中：
1. 尝试每个 Provider 前 → `cb.before_call()` 检查
2. OPEN 时 → 记录 warning + 跳过该 Provider
3. 成功 → `cb.on_success()` 重置
4. 失败 → `cb.on_failure()` 计数

### 不影响

- `InsufficientBalanceError` 不触发熔断（非 Provider 故障）
- `_call_with_retry` 内部重试不受熔断影响（重试在熔断检查之后）

## 健康检查

```
GET /api/v1/admin/provider-health
权限：provider_logs:read（admin + operator）

Response:
{
  "providers": {
    "deepseek": {"state": "CLOSED", "consecutive_failures": 0, "opened_at": null},
    "mock": {"state": "CLOSED", "consecutive_failures": 0, "opened_at": null}
  }
}
```

## 安全

- 熔断状态仅在服务端内存，客户端不可篡改
- 健康检查端点受 `PermissionChecker("provider_logs:read")` 保护
- 不泄露 API Key 或 raw payload

## 测试

```bash
python -m pytest tests/test_circuit_breaker.py -v  # 18 passed
python -m pytest tests/ -v                           # 350 passed, 74 skipped
```

## 残余风险

- 熔断状态仅在内存，服务重启后重置（MVP 可接受）
- 不支持动态调整熔断参数（需修改代码）
- 不持久化故障历史到 provider_call_log（已有调用日志可查询）
- HALF_OPEN 只允许一次探测（无并发控制——多个并发请求可能同时探测）
