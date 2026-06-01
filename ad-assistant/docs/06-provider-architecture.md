# 06 Provider 架构

## 目标

所有模型调用必须通过云端 Provider 层。

禁止前端直接调用第三方 AI API。
禁止 API Key 下发客户端。

## 目录建议

```text
cloud-backend/app/providers/
  base.py
  openai_provider.py
  deepseek_provider.py
  claude_provider.py
  local_provider.py
  comfyui_provider.py
  image_provider.py
  ocr_provider.py
  vector_provider.py
```

## 统一返回结构

所有 Provider 必须返回统一结构：

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "input_units": 0,
  "output_units": 0,
  "image_units": 0,
  "gpu_seconds": 0,
  "raw_cost": 0.0,
  "estimated_cost": 0.0,
  "currency": "CNY",
  "result": {},
  "raw_usage": {}
}
```

## 路由原则

默认路由：
- 普通文本任务优先 DeepSeek
- 高级优化任务使用 GPT 或 Claude
- 图像任务按质量选择本地或云端
- 用户主动选择高级优化时才调用更强模型

路由策略必须在云端执行。

## Provider 扩展规则

新增 Provider 时：
- 只能新增 provider 文件或注册配置
- 不允许大改业务层
- 必须实现统一返回结构
- 必须写入 `provider_call_log`
- 必须记录原始 usage 和估算成本
- 必须支持超时、重试、错误码映射

修改 Provider 接口属于重大变更，必须先确认。

## Provider 调用日志

每次调用必须记录：
- user_id
- device_id
- request_id
- feature
- provider
- model
- input_units
- output_units
- image_units
- gpu_seconds
- raw_cost
- estimated_cost
- credits_charged
- status
- error_code
- created_at

## Provider 路由层 (Sprint-02 Task-09)

Provider 路由层位于 route handler 和 `execute_provider_call` 之间：

```
Route Handler → ProviderRouter.route(feature, plan) → AsyncProvider
                   ↓
            ProviderRegistry.get(name) → MockProvider / future real providers
                   ↓
            execute_provider_call(provider, ...) → ProviderResult
```

### 核心模块

| 模块 | 路径 | 职责 |
|------|------|------|
| `ProviderRegistry` | `app/providers/registry.py` | 按名存取 `AsyncProvider` 实例 |
| `ProviderRouter` | `app/providers/router.py` | 按 (feature, plan) 选择 provider |
| `route_and_execute_provider_call` | `app/services/provider_service.py` | 先路由再执行（高层入口） |

### 路由规则

路由规则通过 `DEFAULT_ROUTING_RULES` 字典配置，映射 `{feature: {plan: provider_name}}`。
当前所有 (feature, plan) 均解析到 `"mock"`。
未知 feature 或 plan 默认回退到 `"mock"`。

### 使用方式

端点应使用 `route_and_execute_provider_call()` 代替直接实例化：

```python
result = await route_and_execute_provider_call(
    db=db, feature="mock_ad_copy", plan=user.plan_code,
    request=provider_request, user_id=user.id, device_id=device.id,
    request_id=request_id,
)
```

原有 `execute_provider_call(provider=..., ...)` 保持不变，支持显式指定 provider。

## Sprint-02 Task-03: Provider Mock Foundation ✅ Implemented

Implemented on branch `feature/sprint-02-task-03-provider-mock`:

- formalized backend Provider base interface (`ProviderRequest`, `ProviderResult`, `AsyncProvider`);
- added deterministic `MockProvider` (`mock` / `mock-text-v1`);
- added mock-only cost estimation (`app/services/cost_service.py`);
- added provider execution/logging helper (`app/services/provider_service.py`);
- 24 focused tests + 126 regression pass.

This task did not add real provider SDKs, public provider routes, provider API keys,
credit deduction, or database migrations.

## Sprint-02 Task-04: Mock AI API Endpoint ✅ Implemented

Implemented on branch `feature/sprint-02-task-04-mock-ai-api`:

- added `POST /api/v1/mock-ai/ad-copy` — first authenticated provider-backed endpoint;
- endpoint calls `MockProvider` through `execute_provider_call`;
- writes `provider_call_log` with `credits_charged=0`;
- propagates `X-Request-ID` to response and provider log;
- does not expose `raw_usage` to clients;
- 21 focused tests + 147 regression pass.

## Sprint-02 Task-09: Provider Routing Design ✅ Implemented

Implemented on branch `feature/sprint-02-task-09-provider-routing`:

- added `ProviderRegistry` (`app/providers/registry.py`) — named container with module-level singleton;
- added `ProviderRouter` (`app/providers/router.py`) — (feature, plan) → provider selection;
- added `route_and_execute_provider_call()` as high-level entry point;
- updated `mock_ai.py` to use routing instead of direct `MockProvider()` instantiation;
- 20 focused routing tests + 147 regression + 21 mock AI tests all pass;
- all routes still resolve to `MockProvider` — no real provider SDKs/keys/network calls;
- `execute_provider_call()` unchanged — still accepts explicit `provider`.
