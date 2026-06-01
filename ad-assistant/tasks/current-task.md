# Sprint-03 Planning — Comprehensive Review Findings & Candidate Tasks

## Status

`PLANNING` — 待用户审阅和确认。

## Background

Sprint-02 已全部收尾（9 tasks + 2 workflow PRs merged）。代码库经过了全面审查，发现了一系列需要处理的问题。本文档汇总审查发现，并规划 Sprint-03 候选任务。

---

## Part 1: 审查发现（C3 汇总）

### 已在当前分支修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `cloud-backend/app/api/v1/credits.py` | 未使用导入 `CreditLedgerItem` | 移除 |
| `cloud-backend/app/services/provider_log_service.py` | 未使用导入 `datetime, timezone` | 移除 |
| `cloud-backend/app/services/usage_service.py` | 未使用导入 `datetime, timezone` | 移除 |
| `cloud-backend/app/main.py` | 局部 `import json` | 提升到文件顶部 |
| `cloud-backend/app/api/v1/auth.py` | 局部 `import hashlib` | 提升到文件顶部 |
| `cloud-backend/app/providers/registry.py` | 不必要的延迟导入 `MockProvider` | 移到顶部 |
| `cloud-backend/app/services/provider_service.py` | 不必要的延迟导入 `get_provider_router` | 移到顶部 |
| `cloud-backend/app/schemas/__init__.py` | 缺少 `credit`、`mock_ai` re-export | 补充完整 |
| `docs/03-monorepo-structure.md` | 目录列表缺 docs 20-25 | 补充 |
| `docs/sprint-01-summary.md` | 候选任务从未更新 | 标注已处理 |
| `docs/development-record.md` | 缺 Task 06-09 记录 | 补充 |
| `PROGRESS.md` | 缺 Task-06 条目 | 补充 |

### 需要后续任务处理的发现

#### P0 — 安全/可靠性

| # | 来源 | 文件 | 问题 | 建议 Sprint-03 任务 |
|---|------|------|------|---------------------|
| D1 | Desktop CRITICAL | `LoginPage.vue`, `authStore.ts` | Device fingerprint 为用户手动输入，完全绕过设备绑定安全机制 | Task: 自动生成 device fingerprint (machine-ID / UUID) |
| D2 | Desktop WARNING | `authStore.ts` + `cloudApi.ts` | Access token 双源存储 (Pinia store + module-level var)，可能漂移 | Task: 统一 token 管理到 Pinia store |
| D3 | Desktop WARNING | `ocrService.ts`, `cloudApi.ts` | 所有 `fetch()` 调用无超时/中断 | Task: 添加 AbortController + 超时 |
| D4 | Backend WARNING | `auth_service.py:_log_risk` | 静默吞没所有异常 (`except Exception: pass`) | Task: 添加 logging.exception |

#### P1 — 类型安全/代码质量

| # | 来源 | 文件 | 问题 | 建议 Sprint-03 任务 |
|---|------|------|------|---------------------|
| D5 | Desktop WARNING | 多处 `.vue`, `.ts` | 所有 catch 块使用不安全的 `err as Type` 断言 | Task: 添加 runtime type guard |
| D6 | Desktop WARNING | `OcrPage.vue` | Blob URL 导航离开时不释放 | Task: onUnmounted cleanup |
| D7 | Desktop INFO | `router.ts` | 无路由级 auth guard，页面短暂闪烁 | Task: router.beforeEach guard |
| D8 | Backend WARNING | `router.py:route()` | `async` 方法但无 await | Task: 改为 sync 或保持（低优先级） |
| D9 | Backend INFO | `core/middleware.py`, `core/auth_deps.py` | 死模块，从未被导入 | Task: 删除或实现 |
| D10 | Backend WARNING | `cost_service.py` | 冗余输入验证（Pydantic 已验证） | Task: 清理 |

#### P2 — 架构/重构

| # | 来源 | 文件 | 问题 | 建议 |
|---|------|------|------|------|
| D11 | Backend CRITICAL | `core/auth_deps.py` | `core` 反向依赖 `api` (架构违规) | Task: 重构 deps 位置 |
| D12 | Backend INFO | `schemas/__init__.py` vs `module-context` | Task 编号历史碰撞 (credit_ledger 原为 Task-02) | 文档说明，不阻塞 |

---

## Part 2: Sprint-03 候选任务

### P0 — 必须做

| Task | 描述 | 优先级理由 |
|------|------|-----------|
| **S03-T01** 修复审查发现 D1-D4 | Device fingerprint、token 双源、fetch 超时、_log_risk 日志 | 安全和可靠性红线 |
| **S03-T02** 第一个真实 Provider 集成 | DeepSeek / OpenAI SDK 接入，API key 管理，真实网络调用 | 核心商业价值 |
| **S03-T03** 真实扣费链路 | `credit_ledger` 写入、`estimated_cost` → 算力换算、余额扣除 | 商业模式闭环 |

### P1 — 应该做

| Task | 描述 | 优先级理由 |
|------|------|-----------|
| **S03-T04** 修复审查发现 D5-D10 | 类型安全、Blob cleanup、auth guard、死代码清理 | 代码质量和 UX |
| **S03-T05** Provider fallback/retry | 多 Provider 容错、健康检查、降级策略 | 生产可用性 |
| **S03-T06** 套餐/支付/充值 | Membership、package、payment、recharge、grant-balance | 商业模式 |

### P2 — 可以做

| Task | 描述 |
|------|------|
| **S03-T07** 修复审查发现 D11-D12 | 架构重构、目录名修正 |
| **S03-T08** 后台管理查询/报表 | Admin query and reporting |
| **S03-T09** OCR 历史记录隐私策略 | Retention、cleanup、privacy policy |
| **S03-T10** 其他端点迁移 `response_model` | 将 `response_model=None` 改为 `response_model=APIResponse[X]` |

---

## 建议执行顺序

```
Sprint-03:
  Phase 1: S03-T01 (安全修复) → S03-T02 (真实 Provider) → S03-T03 (真实扣费)
  Phase 2: S03-T04 (代码质量) → S03-T05 (容错) → S03-T06 (支付)
  Phase 3: S03-T07~T10 (剩余改进)
```

---

## Next Action

请确认：
1. 当前分支 `review/sprint-02-comprehensive-review` 的修改是否可以提交？
2. Sprint-03 的优先级排序是否认可？从哪个 Task 开始？
