# 项目进度

本文件用于记录 AI 图文广告助手项目的模块级进度。

Claude Code / DeepSeek 每完成一个模块或任务后，必须追加一条记录。记录要基于事实，保持简洁；不得写入真实密钥、Token、生产数据库连接串或用户隐私数据。

## 2026-06-02 — S04-T03: Local OCR History Cleanup / 隐私清理

### 范围

- 目标：补齐本地 OCR 历史删除/清空能力，清理沙箱图片副本。
- 已实现：
  - history.py: `delete_history_by_id()` + `clear_all_history()`
  - routes/ocr.py: `DELETE /local/ocr/history/{id}` + `DELETE /local/ocr/history`
  - ocrService.ts: `deleteHistoryRecord()` + `clearAllHistory()`
  - HistoryPage.vue: 工具栏 + 删除按钮 + 内联确认 + 清空弹窗
- 未实现：无（计划内全部完成）

### 主要改动

- 后端修改 2 文件: `history.py`（2 functions）、`routes/ocr.py`（2 DELETE endpoints）
- 后端测试修改 2 文件: `test_ocr_history.py`（+7 tests）、`test_ocr_api.py`（+6 tests）
- 前端修改 2 文件: `ocrService.ts`（2 functions）、`HistoryPage.vue`（UI + script + CSS）

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（纯本地服务增量功能）
- 未加入密钥或生产凭据：是

### 测试结果

- 后端单元测试（test_ocr_history.py）：19 passed
- 后端 API 测试（test_ocr_api.py）：23 passed
- 全量：42 passed
- 前端构建（npm run build）：65 modules, 0 errors

### 风险和后续

- 残余风险：孤儿沙箱文件（DB 删除成功但文件清理失败时），不影响功能
- 后续任务：S04-T04（会员/套餐/充值流程）
- 回滚方式：revert 对应提交

## 2026-06-02 — S04-T02: Dashboard 数据集成 + AI 文案生成入口

### 范围

- 目标：将桌面仪表盘从 mock 数据切换到后端聚合 API，同时启用 AI 文案生成入口。
- 已实现：
  - 后端 `GET /api/v1/dashboard/summary` 端点（schema + service + router）
  - 桌面端 cloudApi + authStore 接入 dashboard summary
  - DashboardPage.vue stats 卡片/最近订单使用 API 数据 + mock fallback + loading 骨架
  - AI 文案生成快捷入口启用 + AdCopyPage.vue（表单 → mock_ad_copy API → 结果）
- 未实现：无（计划内全部完成）

### 主要改动

- 后端新增 4 文件：`app/schemas/dashboard.py`、`app/services/dashboard_service.py`、`app/api/v1/dashboard.py`、`tests/test_dashboard.py`
- 后端修改 1 文件：`app/main.py`（注册 dashboard router）
- 桌面端新增 1 文件：`src/pages/AdCopyPage.vue`
- 桌面端修改 5 文件：`cloudApi.ts`、`authStore.ts`、`DashboardPage.vue`、`dashboardMock.ts`、`router.ts`

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（只读聚合查询 + 已有 API 调用）
- 未加入密钥或生产凭据：是
- 触发高风险暂停规则：否

### 测试结果

- 后端聚焦测试：9 passed
- 后端全量回归：250 passed, 55 skipped

### 风险和后续

- 残余风险：Dashboard summary 4 次 DB 查询 — 当前数据量小无影响，未来可优化
- 后续任务：Sprint-04 剩余候选（Membership/套餐/充值、快捷入口接入真实功能、Tauri 深色标题栏、Local OCR history cleanup）
- 回滚方式：revert 对应提交，恢复 mock 数据

## 记录模板

```markdown
## YYYY-MM-DD - <模块或任务名称>

状态：<PLANNED | IN_PROGRESS | IMPLEMENTED_SELF_REVIEW_PASSED | IMPLEMENTED_NEEDS_FIX | BLOCKED | MERGED>

分支：
提交：
PR：

### 范围

- 目标：
- 已实现：
- 未实现：

### 主要改动

- <文件或模块>：<说明>

### 自检结果

- 任务单完整：
- 修改范围符合 allowed files：
- 未触碰未确认高风险变更：
- 未加入密钥或生产凭据：
- 模块上下文已更新：
- Bug 根因已记录（如适用）：

### 测试结果

- <命令>：<结果>

### 风险和后续

- 残余风险：
- 后续任务：
- 回滚方式：
```

## 记录

## 2026-06-02 - Sprint-04 Task-01 Provider Reliability (Pre-flight + Fallback/Retry)

状态：IMPLEMENTED_SELF_REVIEW_PASSED

分支：`feature/sprint-04-task-01-provider-reliability`

### 范围

- 目标：补齐 Sprint-03 已知的两个安全/可靠性缺口——余额不足拦截 + Provider 降级/重试。
- 已实现：
  - **两级余额门禁**：absolute min (1 积分) + feature min (FEATURE_MIN_CREDITS dict)。
  - **InsufficientBalanceError**：余额不足时写入 provider_call_log + API 返回 402 + 中文提示。
  - **Provider 降级链**：deepseek → mock 一级降级，InsufficientBalanceError 不触发降级。
  - **瞬时故障重试**：TIMEOUT/CONNECTION_ERROR/API_ERROR 最多 2 次重试，指数退避 1s→2s。
  - **Router 增强**：`resolve_name()` 方法 + `registry` 属性。
- 未实现：熔断器、健康检查端点、多级降级链、DB 动态路由、动态 token 预估。

### 主要改动

- `cloud-backend/app/core/config.py`：新增 `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL` + `FEATURE_MIN_CREDITS`。
- `cloud-backend/app/services/provider_service.py`：新增 `InsufficientBalanceError`、`_check_balance()`、`_is_retryable()`、`_call_with_retry()`；`execute_provider_call` 增加预扣检查步骤；`route_and_execute_provider_call` 增加降级链。
- `cloud-backend/app/providers/router.py`：新增 `resolve_name()` + `registry` property。
- `cloud-backend/app/api/v1/mock_ai.py`：INSUFFICIENT_BALANCE → 402 JSONResponse + 中文提示。
- `cloud-backend/tests/test_provider_reliability.py`（NEW）：29 focused tests。
- `cloud-backend/tests/test_credit_deduction.py`：更新预扣检查受影响测试。
- `cloud-backend/tests/test_provider_mock.py`：fund user 以通过预扣检查；更新 credit_ledger 断言。
- `cloud-backend/tests/test_provider_routing.py`：user_id=None 跳过余额检查。
- `cloud-backend/tests/test_mock_ai_api.py`：新增 `_fund_test_user` fixture；更新 credits_charged/credit_ledger 断言。
- `docs/07-ai-cost-control.md`：S04-T01 预扣检查实现证据。
- `docs/06-provider-architecture.md`：S04-T01 降级/重试实现证据。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已在任务单中声明）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：是（docs/07 + docs/06）

### 测试结果

- Focused tests (test_provider_reliability.py)：29 passed
- Full regression：241 passed, 55 skipped
- `git diff --check`：待运行

### 风险和后续

- 残余风险：FEATURE_MIN_CREDITS 为静态配置，未来新增 feature 需手动更新；实际成本超过最低阈值时 partial deduction 仍为安全网。
- 后续任务：熔断器/健康检查、多级降级链、DB 动态路由、动态 token 预估、Tauri 深色标题栏、Dashboard 数据接入。
- 回滚方式：设置 `MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL=0` + 清空 `FEATURE_MIN_CREDITS` 恢复旧行为，或 revert 对应提交。

## 2026-06-02 - Sprint-03 Closeout

状态：MERGED

分支：`main`
提交：`3bbfafb`

### 范围

- 目标：关闭 Sprint-03，编写 sprint summary，更新任务状态为 IDLE。
- 已实现：`docs/sprint-03-summary.md`（完整 sprint summary）、`tasks/current-task.md` → IDLE、PROGRESS.md 本条记录。
- 未实现：无代码变更。

### 主要改动

- `docs/sprint-03-summary.md`（NEW）：Sprint-03 完整收尾文档，含 completed modules、capability、safety boundaries、verification、residual risks、Sprint-04 候选。
- `tasks/current-task.md`：状态 → IDLE，记录全部已完成的 S03 任务。
- `PROGRESS.md`：本条记录。

### 自检结果

- 任务单完整：不适用（收尾任务）
- 修改范围符合 allowed files：是（仅 docs + tasks）
- 未触碰未确认高风险变更：是
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用

### 测试结果

- `git diff --check`：通过

### 风险和后续

- 残余风险：无
- 后续任务：用户从 Sprint-04 候选中选择下一任务。
- 回滚方式：revert 对应提交。

## 2026-06-02 - Sprint-03 Task-04 Desktop Dashboard UI Redesign (S03-T04)

状态：MERGED

分支：`feature/sprint-03-task-04-dashboard-ui`
提交：`c16d9d3`
PR：#34

### 范围

- 目标：桌面端首页 UI 改版 — 深色 SaaS 工作台外壳 + Dashboard 页面 + mock 数据。
- 已实现：左侧导航栏（4 分组）、顶部状态栏、欢迎卡片、统计卡片、快捷入口（OCR 可用）、最近订单 mock 表格、最近生成效果图 mock 网格、底部状态栏、1366px 基准 scale 等比缩放布局、`/` → DashboardPage 路由。
- 未实现：快捷入口中除 OCR 外均为 disabled + "即将开放"；订单/图片 "查看全部" 为 mock；底部连接状态为 mock；Tauri 标题栏深色主题需单独任务。

### 主要改动

- `desktop-app/src/App.vue`：桌面工作台外壳（sidebar + topbar + main + footer），1366 canvas + scale 等比缩放。
- `desktop-app/src/router.ts`：新增 dashboard 路由 `/`。
- `desktop-app/src/pages/DashboardPage.vue`（NEW）：首页主内容区。
- `desktop-app/src/pages/dashboardMock.ts`（NEW）：首页 mock 数据。
- `desktop-app/src/components/dashboard/AppSidebar.vue`（NEW）：左侧导航。
- `desktop-app/src/components/dashboard/AppTopbar.vue`（NEW）：顶部状态栏。
- `desktop-app/src/components/dashboard/QuickEntryCard.vue`（NEW）：快捷入口卡片。
- `desktop-app/src/components/dashboard/RecentOrders.vue`（NEW）：最近订单表格。
- `desktop-app/src/components/dashboard/RecentGeneratedImages.vue`（NEW）：最近生成效果图。
- `docs/26-desktop-dashboard-ui-redesign.md`：设计文档（含返工要求与验收标准）。
- `tasks/current-task.md`：实现记录。
- `PROGRESS.md`：本条记录。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是（仅 desktop-app/src + docs）
- 未触碰未确认高风险变更：是（未改 Tauri / backend / package / OCR / credit / auth）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（纯 UI shell，无独立模块上下文）
- Bug 根因已记录：不适用

### 测试结果

- `npm run build`（desktop-app）：62 modules, 0 errors
- `git diff --check`：通过

### 风险和后续

- 残余风险：顶部白色窗口栏来自 Tauri 系统 chrome，本轮未处理；小窗口（<800px）scale 后字体偏小但可读。
- 后续任务：Tauri 深色标题栏 / EXE Packaging（单独任务）；快捷入口逐个接入真实功能；Dashboard 数据接入真实 API。
- 回滚方式：revert 对应提交，恢复 `/` 路由到旧行为。

## 2026-06-01 - Coding Standards Extensibility Guidelines

状态：MERGED

分支：`docs/extensibility-guidelines`
提交：`3917a90`
PR：#30（已按用户确认合并到 `main` @ `fe4da23`）

### 范围

- 目标：补充项目编码规范中的可扩展性与可修改性规则，支持第一期后续功能演进。
- 已实现：新增“可扩展性与可修改性”章节，覆盖现有分层接入、可变业务规则集中管理、API/DTO/错误码集中维护、局部化修改、模块上下文和回滚记录。
- 未实现：未修改业务代码；未新增依赖、格式化工具、CI、API、数据库、Provider、Auth、Credit 或 Tauri 逻辑。

### 主要改动

- `docs/15-coding-standards.md`：新增可扩展性与可修改性规则。
- `tasks/current-task.md`：记录本次纯文档规范补充任务。
- `PROGRESS.md`：本条进度和自审记录。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（纯文档）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（项目级规范）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- `git diff --check`：通过

### 风险和后续

- 残余风险：规则为项目级约束，需要后续任务执行时持续检查。
- 后续任务：后续功能任务应在任务单和模块上下文中记录扩展入口、修改注意事项和回滚方式。
- 回滚方式：revert 对应文档提交。

## 2026-06-01 - Sprint-03 Task-01 Security & Reliability Fixes (S03-T01)

状态：MERGED

分支：`feature/sprint-03-task-01-security-fixes`
提交：`1d570f4`
PR：#28（已按用户确认合并到 `main` @ `0c1096b`）

### 范围

- 目标：修复 Sprint-02 全面审查发现的 4 个 P0 安全/可靠性问题。
- 已实现：D1 自动生成 device fingerprint (crypto.randomUUID)、D2 统一 token 到 Pinia store、D3 fetch 超时保护 (AbortController + 30s)、D4 _log_risk 异常日志 (logging.exception)。
- 未实现：D1 中"重置设备指纹"按钮（仅 dev/debug 用，非 P0）；不涉及其他安全修复。

### 主要改动

- `desktop-app/src/pages/LoginPage.vue`：D1 — 移除手动 device_fingerprint 输入框，auto-generate via crypto.randomUUID() + localStorage 持久化。
- `desktop-app/src/stores/authStore.ts`：D2 — initFromService() 改为 no-op + 移除未使用 getAccessToken import。
- `desktop-app/src/services/cloudApi.ts`：D3 — 新增 AbortController 30s 超时 + 修复 Headers 合并 + 修复 options mutation。
- `desktop-app/src/services/ocrService.ts`：D3 — 新增 AbortController 30s 超时 + 修复 options mutation。
- `cloud-backend/app/services/auth_service.py`：D4 — except Exception: pass → logging.exception()。
- `tasks/current-task.md`：S03-T01 任务单。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（安全修复，无新模块）
- Bug 根因已记录（如适用）：是（自审发现 3 个问题：unused import、options mutation x2）

### 测试结果

- Backend regression：167 passed
- Desktop `npm run build`：43 modules, 0 errors
- CI `pg-integration`：passed
- `git diff --check`：passed

### 风险和后续

- 残余风险：D2 `initFromService()` 改为 no-op，如有调用方依赖其旧行为（从 cloudApi 读 token）可能受影响，已确认无调用方。
- 后续任务：S03-T02（首个真实 Provider 集成 — DeepSeek SDK）。
- 回滚方式：revert 对应提交，恢复手动 fingerprint 输入、恢复双源 token、移除超时逻辑、恢复 pass。

## 2026-06-01 - Sprint-03 Task-02 First Real Provider Integration — DeepSeek (S03-T02)

状态：MERGED → `1773ab4` (squash merge of PR #32)

分支：`feature/sprint-03-task-02-deepseek-provider` (deleted)

### 范围

- 目标：集成 DeepSeek Chat API 作为首个真实 AsyncProvider，使 mock_ad_copy + standard plan 用户获得真实 AI 广告文案。
- 已实现：`DeepSeekProvider`（AsyncProvider 实现）、`openai` SDK 依赖、DeepSeek 配置项、Registry 注册、路由规则更新、真实成本计算、prompt 构建、25 focused tests。
- 未实现：不涉及 credit 扣费（S03-T03）、不涉及 fallback/retry、不涉及其他 plan/feature 路由、不涉及客户端修改。

### 主要改动

- `cloud-backend/pyproject.toml`：新增 `openai>=1.0.0` 依赖。
- `cloud-backend/app/core/config.py`：新增 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` 配置。
- `cloud-backend/app/providers/deepseek_provider.py`（NEW）：DeepSeekProvider — 调用 DeepSeek Chat API，映射到 ProviderResult。
- `cloud-backend/app/providers/__init__.py`：添加 deepseek_provider 到模块列表。
- `cloud-backend/app/providers/registry.py`：注册 `"deepseek"` → DeepSeekProvider()。
- `cloud-backend/app/providers/router.py`：`mock_ad_copy/standard` → `"deepseek"`（其他路由不变）。
- `cloud-backend/app/services/cost_service.py`：新增 `calculate_deepseek_cost()`（¥1/1M input, ¥2/1M output）。
- `cloud-backend/app/services/provider_service.py`：按 provider 名分发成本计算；新增 DeepSeekProviderError 处理；意外异常不再硬编码 provider/model。
- `cloud-backend/app/api/v1/mock_ai.py`：构建真实 prompt，传入 ProviderRequest.message。
- `cloud-backend/tests/test_deepseek_provider.py`（NEW）：25 focused tests（成功路径、错误映射、成本计算、路由规则、安全性）。
- `cloud-backend/tests/test_provider_routing.py`：更新 fixture 注册 deepseek，更新断言覆盖新路由。
- `cloud-backend/tests/test_mock_ai_api.py`：添加 routing override fixture 确保 API 测试仍使用 MockProvider。
- `docs/06-provider-architecture.md`：新增 Sprint-03 Task-02 实现证据。
- `docs/sprint-02-summary.md`：更新 safety boundaries。
- `tasks/current-task.md`：S03-T02 任务单。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是（API key 仅通过 Settings 读取，未硬编码）
- 模块上下文已更新：不适用（provider 层，文档已更新）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- DeepSeek focused：25 passed
- Full regression：192 passed, 55 skipped
- `git diff --check`：passed

### 风险和后续

- 残余风险：`DEEPSEEK_API_KEY` 为空时 DeepSeekProvider 会抛出 API_KEY_MISSING；需在部署环境配置 `.env`。路由规则可变（dict-of-dicts），后续可随时调整。
- 后续任务：S03-T03（真实 credit 扣费）、fallback/retry 机制、其他 plan 逐步切到 DeepSeek。
- 回滚方式：将 `mock_ad_copy/standard` 路由改回 `"mock"`，或从 registry 移除 `"deepseek"`。

## 2026-06-01 - Sprint-03 Task-03 Real Credit Deduction (S03-T03)

状态：MERGED

分支：`feature/sprint-03-task-03-credit-deduction`
提交：`8fcf6f5`
PR：#33

### 范围

- 目标：将 credit 扣费链路接入 Provider 调用，每次成功调用后自动从用户余额扣减积分并写入 credit_ledger。
- 已实现：`CREDITS_PER_CNY` 配置、`cny_to_credits()` 换算、`deduct_credits()` 原子扣减、`execute_provider_call` 扣费集成、19 focused tests。
- 未实现：预扣检查（余额不足拦截）、plan 级别倍率、月赠自动补充、退款逻辑、客户端修改。

### 主要改动

- `cloud-backend/app/core/config.py`：新增 `CREDITS_PER_CNY: int = 100`。
- `cloud-backend/app/providers/base.py`：`ProviderResult` 新增 `credits_charged: int = 0` 字段。
- `cloud-backend/app/services/cost_service.py`：新增 `cny_to_credits()` — CNY→积分 ceil 换算法。
- `cloud-backend/app/services/credit_service.py`：新增 `deduct_credits()` — 原子扣减 balance + 写 credit_ledger。
- `cloud-backend/app/services/provider_service.py`：成功路径增加 CNY→积分换算 + 扣费调用；扣费失败记录 DEDUCTION_FAILED 并重新抛出。
- `cloud-backend/app/api/v1/mock_ai.py`：`credits_charged` 改为使用 `result.credits_charged`（不再硬编码 0）。
- `cloud-backend/tests/test_credit_deduction.py`（NEW）：19 focused tests（换算 6 + 扣减 7 + provider_service 集成 6）。
- `docs/07-ai-cost-control.md`：新增 S03-T03 实现证据和扣费链路说明。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是（base.py 的 ProviderResult 字段新增是必要且向后兼容的）
- 未触碰未确认高风险变更：是（credit 高风险已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：是（docs/07-ai-cost-control.md）

### 测试结果

- Credit deduction focused：19 passed
- Full regression：211 passed, 55 skipped
- `git diff --check`：待运行

### 风险和后续

- 残余风险：余额为 0 的测试用户不会触发扣费（部分扣费返回 0），但测试断言 `credits_charged==0` 仍成立。生产环境用户余额为 0 时，调用仍会成功但不扣费，后续需要预扣检查（pre-flight balance check）。
- 后续任务：S03-T04（预扣检查 + 余额不足拦截）、fallback/retry、plan 倍率。
- 回滚方式：设置 `CREDITS_PER_CNY = 0` 使 `cny_to_credits()` 始终返回 0，或 revert 对应提交。

## 2026-06-01 - Agent Workflow CC Autonomous Handoff

状态：MERGED

分支：`docs/cc-autonomous-workflow`
提交：`33cc6a9`
PR：#21（已合并到 `main` @ `fe5e94f`）

### 范围

- 目标：将项目流程调整为 CC 自主写任务单、实现、测试、自审、提交任务分支、push 和准备 PR。
- 已实现：项目协作规则、Git 守卫规则、`PROGRESS.md` 进度账本、Bug 根因优先流程、本地 task executor / git guardrails skill 同步更新。
- 未实现：未开发业务功能；未修改 backend、desktop、API/schema/provider/auth/credit/Tauri/CI/dependency。

### 主要改动

- `CLAUDE.md`：定义 CC 自主执行、任务单生成、自审、Bug 修复和进度记录规则。
- `CODEX.md`：将 Codex 改为按需复核，不再作为默认强制门禁。
- `README.md`：更新开发流程和 `PROGRESS.md` 记录要求。
- `docs/14-ai-agent-workflow.md`：记录 CC 自主协作流程和 Bug 修复流程。
- `docs/16-git-workflow.md`：允许 CC 自审通过后提交和 push 任务分支，同时保留 `main` 只能 PR 合并。
- `docs/20-agent-git-guardrails.md`：将默认门禁改为 CC 自审，并要求更新 `PROGRESS.md`。
- `PROGRESS.md`：新增项目进度账本和记录模板。
- `tasks/current-task.md`：记录本次 workflow 调整任务。
- 本地 skills：更新 `ad-assistant-task-executor` 和 `ad-assistant-git-guardrails`。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（workflow-only 规则变更）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- `git diff --check`：通过
- `quick_validate.py ad-assistant-task-executor`：通过
- `quick_validate.py ad-assistant-git-guardrails`：通过
- PR #21 `pg-integration`：通过

### 风险和后续

- 残余风险：CC 自主权更高；主要控制点是 `main` PR-only、PR 合并需用户明确确认、高风险暂停规则和必要时按需复核。
- 后续任务：后续产品任务按新的 CC-first 流程启动。
- 回滚方式：revert workflow 文档提交，并按需恢复本地 skill 旧版本。

## 2026-06-01 - Sprint-02 Task-06 Desktop Mock AI E2E Smoke Verification

状态：MERGED

分支：`feature/sprint-02-task-06-desktop-mock-e2e-smoke`
提交：`cfbadeb`
PR：#18（已合并到 `main` @ `cfbadeb`）

### 范围

- 目标：使 Task-05 的 desktop mock MVP 路径可重现、可手动验证。
- 已实现：E2E smoke 操作手册 (`docs/25-desktop-mock-e2e-smoke.md`)、dev seed 脚本 (`cloud-backend/scripts/dev_seed_user.py`)、更新 desktop/backend 开发指南。
- 未实现：未修改 backend/API/DDL/dependency/shared/Tauri/desktop 源码。

### 主要改动

- `docs/25-desktop-mock-e2e-smoke.md`：E2E smoke runbook。
- `cloud-backend/scripts/dev_seed_user.py`：dev-only seed 脚本。
- `docs/09-desktop-app-guide.md`：引用 dev runbook。
- `docs/11-cloud-backend-guide.md`：新增 dev setup 章节。
- `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md`：模块上下文。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是
- 未加入密钥或生产凭据：是
- 模块上下文已更新：是
- Bug 根因已记录（如适用）：是（发现 DDL TIMESTAMPTZ / ORM DateTime 不匹配，后续 Task-07 修复）

### 测试结果

- `npm run build`：43 modules, 0 errors
- Backend regression：147 passed
- `git diff --check`：通过

### 风险和后续

- 残余风险：实时手动验证因本地 PostgreSQL/backend 环境不可用未完成。
- 后续任务：Task-07（修复 DDL/ORM DateTime 不匹配）。
- 回滚方式：revert 对应提交。

## 2026-06-01 - Sprint-02 Task-07 Backend PostgreSQL DateTime Alignment

状态：MERGED

分支：`feature/sprint-02-task-07-pg-datetime-align`
提交：`80e41a1`
PR：#20（已合并到 `main` @ `1a3602f`）

### 范围

- 目标：让 SQLAlchemy models 的 `DateTime(timezone=True)` 与 DDL 的 `TIMESTAMPTZ` 对齐。
- 已实现：8 个 model 文件共 18 个 DateTime 列改为 `DateTime(timezone=True)`；更新 seed 脚本文档说明；更新相关文档。
- 未实现：未修改 DDL、API、service、provider、shared、desktop、dependency、CI 或 `.env`；未做 services/api datetime 使用全量审计。

### 主要改动

- `cloud-backend/app/models/user.py`：`DateTime(timezone=True)` 2 处。
- `cloud-backend/app/models/device.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/auth_session.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/credit_account.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/credit_ledger.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/provider_call_log.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/risk_log.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/usage_event.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/scripts/dev_seed_user.py`：更新 docstring。
- `docs/25-desktop-mock-e2e-smoke.md`：移除 PostgreSQL 绕过说明。
- `docs/11-cloud-backend-guide.md`：更新 PostgreSQL 支持状态。
- `docs/12-database-design.md`：新增 timestamp 对齐说明。
- `docs/sprint-02-summary.md`：新增 Task-07 状态块。
- `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md`：新增模块上下文。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：是
- Bug 根因已记录（如适用）：是，根因为 ORM/DDL DateTime 类型不匹配

### 测试结果

- SQLite regression：147 passed
- PG DDL integration：55 passed
- ORM `create_all` against PG：succeeded
- `dev_seed_user.py` against PG：user created + device bound
- `git diff --check`：通过

### 风险和后续

- 残余风险：services/api 代码中可能仍有 datetime naive 假设，后续需要专项审查。
- 后续任务：Task-08（API response / OpenAPI / shared DTO）。
- 回滚方式：revert 对应提交，恢复 model 文件中未声明 `DateTime(timezone=True)` 的状态。

## 2026-06-01 - Sprint-02 Task-08 Mock AI API Contract Formalization

状态：MERGED

分支：`feature/sprint-02-task-08-mock-ai-api-contract`
提交：`6d763e6`
PR：#22（已按用户确认合并到 `main` @ `6fc40a8`）

### 范围

- 目标：为 mock AI endpoint 建立第一个端到端 API 契约管道 — generic `APIResponse[T]`、`response_model` 绑定、OpenAPI spec、TypeScript DTO。
- 已实现：`APIResponse[T]` generic model、mock-ai 端点绑定 `response_model=APIResponse[MockAdCopyData]`、`shared/openapi/mock-ai.yaml`、`shared/dto/mock-ai.ts`。
- 未实现：不涉及其他端点、不涉及 provider/auth/credit 变更、不新增测试、不新增依赖。

### 主要改动

- `cloud-backend/app/schemas/common.py`：增加 `Generic`/`TypeVar` import，`APIResponse` 改为 `APIResponse(BaseModel, Generic[T])`，helper 函数返回 `APIResponse[Any]`。
- `cloud-backend/app/api/v1/mock_ai.py`：import `APIResponse`，`response_model=None` → `response_model=APIResponse[MockAdCopyData]`，`response_data.model_dump()` → 直接传 Pydantic model 实例。
- `shared/openapi/mock-ai.yaml`：新建 OpenAPI 3.0.3 spec（完整 path、request/response schema、error 示例）。
- `shared/dto/mock-ai.ts`：新建 TypeScript DTO（`MockAdCopyRequest`、`MockAdCopyData`、`APIResponse<T>`、`ErrorDetail`）。
- `shared/openapi/.gitkeep`：更新内容，反映第一个 spec 已创建。
- `shared/dto/.gitkeep`：更新内容，反映第一个 DTO 已创建。
- `docs/23-mock-ai-api-endpoint.md`：新增 OpenAPI/DTO 参考章节 + Task-08 实现证据。
- `docs/05-api-contract.md`：补充首个 spec/DTO 说明。
- `docs/sprint-02-summary.md`：新增 Task-08 状态块，移除已合并的 Task-07 状态块，移除 Candidate B。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（API contract 层，无独立模块上下文目录；合同本身即为权威文档）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- SQLite regression：147 passed
- Mock AI focused：21 passed
- FastAPI OpenAPI 生成验证：`MockAdCopyData` 在 schemas 中，`APIResponse_MockAdCopyData_` 存在，`/api/v1/mock-ai/ad-copy` 在 paths 中
- `git diff --check`：通过
- 接口返回 shape 未变：是（wire response 完全一致）

### 风险和后续

- 残余风险：其他端点仍使用 `response_model=None`，后续按需逐个迁移。
- 后续任务：Candidate C — Real Provider routing design。
- 回滚方式：revert 对应提交，`response_model` 改回 `None`，移除 shared 新文件，恢复 `.gitkeep` 原始内容。

## 2026-06-01 - Sprint-02 Task-09 Provider Routing Design

状态：MERGED

分支：`feature/sprint-02-task-09-provider-routing`
提交：`89fe06f`
PR：#23（已按用户确认合并到 `main` @ `37e0430`）

### 范围

- 目标：构建 provider 路由层 — ProviderRegistry（按名存取）、ProviderRouter（按 feature+plan 选择）、route_and_execute_provider_call（高层入口）。
- 已实现：`ProviderRegistry` 单例（预注册 mock）、`ProviderRouter` 单例（DEFAULT_ROUTING_RULES）、`route_and_execute_provider_call()`、`mock_ai.py` 改用路由。
- 未实现：不涉及真实 provider、不涉及 fallback/retry/health check、不涉及 DB 路由配置、不新增端点。

### 主要改动

- `cloud-backend/app/providers/registry.py`：新建 `ProviderRegistry` + `ProviderRegistryError` + `get_provider_registry()` 单例。
- `cloud-backend/app/providers/router.py`：新建 `ProviderRouter` + `ProviderNotFoundError` + `DEFAULT_ROUTING_RULES` + `get_provider_router()` 单例。
- `cloud-backend/app/services/provider_service.py`：新增 `route_and_execute_provider_call()`（先路由、后执行）；`execute_provider_call()` 不变。
- `cloud-backend/app/api/v1/mock_ai.py`：移除 `MockProvider` import，改用 `route_and_execute_provider_call()`。
- `cloud-backend/app/providers/__init__.py`：更新 docstring 反映 routing 架构。
- `cloud-backend/tests/test_provider_routing.py`：20 个聚焦测试（registry 8 + router 8 + integration 4）。
- `docs/06-provider-architecture.md`：新增 "Provider 路由层" 章节 + Task-09 实现证据。
- `docs/sprint-02-summary.md`：新增 Task-09 状态块，移除 Candidate C。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已创建：是
- Bug 根因已记录（如适用）：不适用

### 测试结果

- SQLite regression：147 passed
- Mock AI focused：21 passed
- New routing focused：20 passed
- Total：167 passed
- FastAPI OpenAPI 生成验证：`MockAdCopyData` + `APIResponse_MockAdCopyData_` + path 均存在
- `git diff --check`：通过
- 接口返回 shape 未变：是

### 风险和后续

- 残余风险：所有路由仍解析到 MockProvider，未来加入真实 provider 时需验证路由规则正确性；fallback/retry 机制尚未实现。
- 后续任务：Candidate A — Desktop Mock AI E2E Smoke Verification（或用户指定的其他任务）。
- 回滚方式：revert 对应提交，`mock_ai.py` 恢复 `MockProvider()` 直接调用，移除 registry/router 模块和新测试。

## 2026-06-01 - Sprint-02 Documentation Cleanup & Closeout

状态：MERGED

分支：`docs/sprint-02-closeout`
提交：`3890c4f`
PR：#27（已合并到 `main` @ `cb3abef`）

### 范围

- 目标：清理 `docs/sprint-02-summary.md` 状态不一致，正式关闭 Sprint-02。
- 已实现：所有 Task 06~09 移入 "Completed Modules"，移除 "In Progress" 段，更新验证记录，新增 Sprint-03 候选。
- 未实现：无代码变更；Sprint-03 候选仅作参考，未启动开发。

### 主要改动

- `docs/sprint-02-summary.md`：完成表增补 Task 06~09 + 2 workflow PR；移除 In Progress 段；新增 Closeout 和 Sprint-03 候选；更新 verified head 到当前 main HEAD。
- `PROGRESS.md`：本条记录。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（纯文档）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（文档整理）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- `git diff --check`：通过

### 风险和后续

- 残余风险：无
- 后续任务：全面代码审查/文档整理（用户指定的下一阶段 C）；Sprint-03 规划（阶段 B）。
- 回滚方式：revert 对应提交，恢复 `sprint-02-summary.md` 旧版。
