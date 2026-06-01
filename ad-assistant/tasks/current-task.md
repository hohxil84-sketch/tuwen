# Current Task: S04-T02 — Dashboard 数据集成 + AI 文案生成入口

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED` — 自审通过，待提交。

## 背景

Sprint-03 Task-04 完成了桌面仪表盘 UI 重构（暗色工作台风格），但仪表盘上的所有数据均为 mock 常量。现在后端已有：

- `CreditAccount` — 用户真实余额
- `ProviderCallLog` — 每次 AI 调用的完整日志（含 feature、provider、status、credits_charged、created_at）
- `UsageEvent` — 功能使用事件

本任务将仪表盘数据从 mock 切换到真实后端聚合接口。同时，S04-T01 完成后 `mock_ad_copy` 端点已具备完整的预扣检查+降级+重试能力，可以安全地对真实用户开放，因此同时启用"AI 文案生成"快捷入口。

## 本次只开发什么

### Part A: 后端 Dashboard Summary 聚合接口

- 新增 `GET /api/v1/dashboard/summary` 端点（需要 auth + device）
- 聚合查询返回：
  - `credit_balance` — 来自 `CreditAccount.balance`
  - `today_calls` — 今日 `ProviderCallLog` 调用次数（status='success'）
  - `monthly_calls` — 本月 `ProviderCallLog` 调用次数（status='success'）
  - `plan_code` — 来自 `CreditAccount.plan_code`（或 `user.plan_code` fallback）
  - `recent_activity` — 最近 5 条 `ProviderCallLog`（feature、provider、model、status、credits_charged、created_at）
- 新增 schema `DashboardSummaryData`、`RecentActivityItem`
- 新增 service 函数 `get_dashboard_summary(db, user_id)`
- 注册 router 到 `main.py`

### Part B: 桌面端 API 调用 + Store

- `cloudApi.ts` 新增 `DashboardSummaryData` 类型和 `dashboardSummary()` 函数
- `authStore.ts` 新增 `dashboardSummary` state + `fetchDashboardSummary()` action

### Part C: 仪表盘数据替换

- `DashboardPage.vue`：stats 卡片和最近订单改为从 API 加载
- 添加 loading 骨架和错误 fallback（失败时回退到 mock 数据）
- 保留 mock 数据作为 fallback
- "最近生成效果图"保持 mock（无图片生成能力）

### Part D: 启用 AI 文案生成入口

- `dashboardMock.ts`：AI 文案生成从 `disabled: true` → `disabled: false`，route 指向 `/ai-ad-copy`
- 新增 `AdCopyPage.vue`：简单的广告文案生成页面（表单 + API 调用 + 结果展示）
- `router.ts`：新增 `/ai-ad-copy` 路由

## 本次不开发什么

- 不做订单管理系统（订单仍是 mock）
- 不做图片生成相关功能
- 不修改数据库 schema / DDL / migration
- 不修改 Provider / 路由 / 扣费逻辑
- 不修改 Tauri / 构建配置
- 不新增后端依赖
- 不做快捷入口以外的功能页面（OCR 已有，其他保持 disabled）
- 不做会员等级/套餐的真实查询（plan_code 显示真实值，但等级名称映射保持简单）

## 允许修改哪些文件

### 后端
- `cloud-backend/app/schemas/dashboard.py` (NEW) — DashboardSummaryData schema
- `cloud-backend/app/services/dashboard_service.py` (NEW) — 聚合查询逻辑
- `cloud-backend/app/api/v1/dashboard.py` (NEW) — API 端点
- `cloud-backend/app/main.py` — 注册 dashboard router
- `cloud-backend/tests/test_dashboard.py` (NEW) — 聚焦测试

### 桌面端
- `desktop-app/src/services/cloudApi.ts` — 新增 dashboardSummary()
- `desktop-app/src/stores/authStore.ts` — 新增 dashboard state/action
- `desktop-app/src/pages/DashboardPage.vue` — 替换 mock 为 API
- `desktop-app/src/pages/dashboardMock.ts` — 更新 AI 文案生成入口
- `desktop-app/src/router.ts` — 新增 /ai-ad-copy 路由
- `desktop-app/src/pages/AdCopyPage.vue` (NEW) — AI 文案生成页面

### 文档
- `tasks/current-task.md` — 实现记录
- `PROGRESS.md` — 进度记录

## 禁止修改哪些文件

- `cloud-backend/app/models/` — 不修改数据库模型
- `cloud-backend/app/providers/` — 不修改 Provider 层
- `cloud-backend/app/services/provider_service.py` — 不修改
- `cloud-backend/app/services/credit_service.py` — 不修改
- `cloud-backend/app/services/cost_service.py` — 不修改
- `cloud-backend/app/api/v1/mock_ai.py` — 不修改
- `cloud-backend/pyproject.toml` — 不新增依赖
- `desktop-app/package.json` — 不新增依赖
- `desktop-app/src-tauri/` — 不修改 Tauri 配置
- `shared/` — 全部禁止

## 验收标准

### Part A
- [ ] `GET /api/v1/dashboard/summary` 返回 200，含 credit_balance、today_calls、monthly_calls、plan_code、recent_activity
- [ ] 未登录返回 401
- [ ] recent_activity 最多 5 条，按时间倒序
- [ ] 用户无 CreditAccount 时 credit_balance=0，plan_code 取自 user.plan_code

### Part B
- [ ] cloudApi.ts 有 DashboardSummaryData 类型和 dashboardSummary() 函数
- [ ] authStore 有 dashboardSummary state 和 fetchDashboardSummary action

### Part C
- [ ] 仪表盘 stats 卡片显示真实余额/今日调用次数/本月调用次数/plan_code
- [ ] "最近订单"显示真实 provider_call_log 最近记录
- [ ] API 失败时回退到 mock 数据
- [ ] 加载中有 loading 状态

### Part D
- [ ] AI 文案生成快捷入口可点击，跳转到 /ai-ad-copy
- [ ] AdCopyPage 可输入产品信息并调用 mock_ad_copy API
- [ ] 调用成功显示结果，失败显示错误信息

### 通用
- [ ] 所有新功能有测试覆盖
- [ ] 现有回归测试全部通过
- [ ] 不新增依赖
- [ ] 不修改数据库 schema

## 测试方式

```bash
# 后端聚焦测试
cd ad-assistant/cloud-backend
python -m pytest tests/test_dashboard.py -v -x

# 全量回归
python -m pytest tests/ -v --ignore=tests/test_pg_integration.py
```

## 是否允许新增依赖

不允许。后端使用已有的 FastAPI、SQLAlchemy、Pydantic；桌面端使用已有的 Vue 3、Pinia、TypeScript。

## 是否涉及重大变更

**否** — 不涉及高风险边界：
- 不修改数据库 schema
- 不修改扣费/支付逻辑
- 不修改 Provider 接口
- 不修改 Auth/Token 模型
- 仅新增只读查询端点 + 桌面端数据替换 + 新增 AI 文案生成页面（使用已有 API）

## 安全检查

- [ ] 不下发 API Key 到客户端
- [ ] 不由客户端扣点
- [ ] 不由客户端决定套餐
- [ ] 不绕过云端授权
- [ ] 不明文保存 Token
- [ ] Dashboard summary 仅返回当前用户数据，无跨用户泄漏

## 风险点

1. **查询性能**：Dashboard summary 执行多次 DB 查询（balance + today_calls + monthly_calls + recent_activity）。当前用户量和数据量小，不存在性能问题。
2. **CreditAccount 不存在**：需处理用户无 CreditAccount 的情况（返回 balance=0，plan_code 取自 user）。
3. **桌面端路由**：AdCopyPage 需要 auth，未登录时需处理（显示登录提示或跳转）。

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

---

## 实现记录 (2026-06-02)

### 修改文件

**后端（新增）**
- `cloud-backend/app/schemas/dashboard.py` — `DashboardSummaryData` + `RecentActivityItem` schema
- `cloud-backend/app/services/dashboard_service.py` — `get_dashboard_summary()` 聚合查询
- `cloud-backend/app/api/v1/dashboard.py` — `GET /api/v1/dashboard/summary` 端点
- `cloud-backend/tests/test_dashboard.py` — 9 个聚焦测试

**后端（修改）**
- `cloud-backend/app/main.py` — 注册 dashboard router

**桌面端（新增）**
- `desktop-app/src/pages/AdCopyPage.vue` — AI 文案生成页面（表单 + API 调用 + 结果展示）

**桌面端（修改）**
- `desktop-app/src/services/cloudApi.ts` — 新增 `DashboardSummaryData` / `RecentActivityItem` 类型 + `dashboardSummary()` 函数
- `desktop-app/src/stores/authStore.ts` — 新增 `dashboardLoading` / `dashboardError` / `dashboardData` state + `fetchDashboardSummary()` action
- `desktop-app/src/pages/DashboardPage.vue` — stats 卡片和最近订单改用 API 数据，添加 loading 骨架和 mock fallback
- `desktop-app/src/pages/dashboardMock.ts` — AI 文案生成从 disabled 改为可用，route = `/ai-ad-copy`
- `desktop-app/src/router.ts` — 新增 `/ai-ad-copy` 路由

**文档**
- `tasks/current-task.md` — 实现记录
- `PROGRESS.md` — 进度记录

### 实现内容

**Part A: 后端 — 全部完成**
- `GET /api/v1/dashboard/summary` 端点，需要 auth + device
- 聚合返回 credit_balance、today_calls、monthly_calls、plan_code、recent_activity (最近 5 条)
- 无 CreditAccount 时 credit_balance=0，plan_code 取自 user.plan_code fallback
- today_calls / monthly_calls 只统计 status='success' 的记录
- 用户数据隔离（只查当前 user_id）

**Part B: 桌面端 API + Store — 全部完成**
- cloudApi.ts 新增 `dashboardSummary()` 和类型定义
- authStore.ts 新增 dashboard state 和 `fetchDashboardSummary()` action

**Part C: 仪表盘数据替换 — 全部完成**
- 4 个 stat 卡片：今日使用次数、剩余额度、本月调用、会员等级，均从 API 数据计算
- "最近订单"表格：从 recent_activity 映射显示
- loading 骨架屏（skeleton shimmer）
- API 失败/mock fallback（dashboardData 为 null 时使用 MOCK_STATS / MOCK_RECENT_ORDERS）

**Part D: AI 文案生成入口 — 全部完成**
- AI 文案生成快捷入口启用，跳转到 `/ai-ad-copy`
- AdCopyPage.vue：产品名称 + 卖点 + 平台 + 风格 → 调用 mock_ad_copy API → 展示结果
- 未登录状态显示登录提示
- 调用失败显示中文错误

### 未实现内容

- 不涉及（所有计划内容已实现）

### 自审结论

- 只实现了 tasks/current-task.md 允许的内容：是
- 只修改了 allowed files：是
- 未混入无关文件：是
- 未新增依赖：是
- 未触碰高风险边界：是（只读聚合查询 + 已有 API 调用）
- 未存储 secrets/密钥/Token：是
- 测试覆盖：9 个聚焦测试全部通过
- 回归测试：250 passed, 55 skipped
- 模块上下文：不适用（本任务不涉及现有模块核心逻辑修改）
- PROGRESS.md 已更新：是

### 测试结果

```
# 聚焦测试
cd cloud-backend
python -m pytest tests/test_dashboard.py -v -x
9 passed

# 全量回归
python -m pytest tests/ -v --ignore=tests/test_pg_integration.py
250 passed, 55 skipped
```

### 是否触发高风险暂停规则

否。

### 风险和回滚方式

1. **Dashboard summary 查询性能**：执行 4 次 DB 查询（balance + today + monthly + recent）。
   - 当前数据量极小，无性能问题。
   - 未来可合并查询或添加缓存。
2. **AdCopyPage 错误处理**：依赖现有 `sanitizeApiError` 映射。
   - INSUFFICIENT_BALANCE (402) 的错误消息已包含中文提示。
3. **回滚方式**：revert 对应提交，DashboardPage.vue 恢复纯 mock 数据。
