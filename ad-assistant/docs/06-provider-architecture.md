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

## Sprint-02 Task-03: Provider Mock Foundation ✅ Implemented

Implemented on branch `feature/sprint-02-task-03-provider-mock`:

- formalized backend Provider base interface (`ProviderRequest`, `ProviderResult`, `AsyncProvider`);
- added deterministic `MockProvider` (`mock` / `mock-text-v1`);
- added mock-only cost estimation (`app/services/cost_service.py`);
- added provider execution/logging helper (`app/services/provider_service.py`);
- 24 focused tests + 126 regression pass.

This task did not add real provider SDKs, public provider routes, provider API keys,
credit deduction, or database migrations.
