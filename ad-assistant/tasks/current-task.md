# S05-R02: 基础后台最小可用管理台

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-02-basic-admin`

## 完成摘要

- 后端新增 5 个只读 GET endpoint：`/api/v1/admin/users|orders|credit-accounts|provider-logs|usage-events`
- 复用 `get_admin_user` 依赖，非管理员 403；敏感字段排除（password_hash/raw_usage/raw_response/metadata_json）
- `admin_service.py`（NEW）：5 个查询方法 + _paginate helper
- `test_admin.py`（NEW）：12 tests（权限隔离 5 + admin 访问 5 + 分页 2）
- AdminPage.vue（NEW）：5 tab 页签 + 表格 + 分页 + 4 状态处理
- Sidebar 新增"管理后台"入口（始终可见，权限服务端判断）
- 后端回归：305 passed, 74 skipped；前端构建：77 modules, 0 errors
- 未修改 DDL、models、Provider、Credit、Payment、config、CI、依赖

## 背景

P0 MVP 包含"基础后台"。当前已有：
- `ADMIN_USER_IDS` 白名单配置
- `get_admin_user()` 依赖注入（检查 user_id ∈ ADMIN_USER_IDS，否则 403）
- `POST /api/v1/admin/credits/grant`（积分赠送，已有）

但缺少可用的管理界面。用户、订单、积分账户、Provider 调用日志、使用事件仍只能靠数据库或 API 直接排查。S05-R02 补齐最小只读管理台。

## 用户目标

管理员登录桌面端后，可进入管理后台，查看用户、充值订单、积分账户、Provider 调用日志和使用事件的只读列表。

## What To Build

### 后端 — 5 个只读 Admin Query Endpoint

所有端点统一前缀 `/api/v1/admin`，复用 `get_admin_user` 依赖，非管理员返回 403。

| # | 端点 | 说明 | 数据来源 |
|---|------|------|---------|
| 1 | `GET /api/v1/admin/users` | 用户列表（id, account, plan_code, created_at），支持 limit/offset | users 表 |
| 2 | `GET /api/v1/admin/orders` | 充值订单列表（id, user_id, plan_code, amount_cny, credits, status, created_at），支持 limit/offset | recharge_orders 表 |
| 3 | `GET /api/v1/admin/credit-accounts` | 积分账户列表（user_id, balance, plan_code, created_at），支持 limit/offset | credit_accounts 表 |
| 4 | `GET /api/v1/admin/provider-logs` | Provider 调用日志（id, user_id, feature, provider, model, status, credits_charged, created_at），支持 limit/offset | provider_call_log 表 |
| 5 | `GET /api/v1/admin/usage-events` | 使用事件列表（id, user_id, feature, created_at），支持 limit/offset | usage_events 表 |

响应格式：统一 `{success, data: {items: [...], total, limit, offset}, error, request_id}`。

### 后端 — Schema + Service + Router

- `app/schemas/admin.py`：新增 5 个响应 schema + 通用分页 schema
- `app/services/admin_service.py`（NEW）：5 个只读查询方法
- `app/api/v1/admin.py`：新增 5 个 GET endpoint
- 不新增 SQLAlchemy model，不修改 DDL

### 桌面端 — AdminPage

- `desktop-app/src/pages/AdminPage.vue`（NEW）：
  - 5 个 tab 页签：用户 / 订单 / 积分账户 / Provider 日志 / 使用事件
  - 每个 tab 内：表格展示（关键列）+ 加载状态 + 错误提示 + 空状态
  - 通用分页：上一页/下一页 + 当前页信息
- `desktop-app/src/services/cloudApi.ts`：新增 5 个 admin API 函数 + DTO 类型
- `desktop-app/src/router.ts`：新增 `/admin` 路由
- `desktop-app/src/components/dashboard/AppSidebar.vue`：新增"管理后台"导航项（仅管理员可见）
- `desktop-app/src/stores/authStore.ts`：新增 `isAdmin` computed + admin API 调用方法

### 管理员可见性

- `authStore` 新增 `isAdmin` computed：检查当前用户 `user.id` 是否在后端返回的管理员列表中
- 由于前端不知道 ADMIN_USER_IDS 配置，采用"调用 admin API 试探"方式：首次进入 admin 页面或 sidebar 渲染时尝试调用 admin users 端点，若返回 200 则可见，若返回 403 则隐藏
- 或更简单：在 sidebar 始终显示管理后台入口，点击进入后若 403 则显示"无权限"

**决策**: 采用简易方案 — sidebar 始终显示"管理后台"（方便后续 RBAC 迁移），admin API 403 时页面显示"无管理权限"而非白屏。这样不依赖前端预知管理员身份。

### 文档

- `docs/module-context/sprint-05-risk-02-basic-admin/context.md`（NEW）：记录端点列表、权限模型、UI 结构、限制和扩展点
- 不需要更新 `docs/09-desktop-app-guide.md`（admin 不在桌面端面向普通用户的功能范围内）

### 进度记录

- 追加更新 `PROGRESS.md`
- 更新 `tasks/current-task.md` 完成后状态

## What Not To Build

- 不做 RBAC 角色体系（那是 S05-R03）
- 不做增删改操作（只读列表），不修改用户、不封禁设备、不退款
- 不做复杂筛选、搜索、排序（只做分页）
- 不做数据导出（CSV/Excel）
- 不做统计图表或 dashboard 摘要
- 不新增数据库表或修改 DDL
- 不修改 Provider 路由、真实 AI 调用、扣费逻辑或套餐规则
- 不接入真实支付或修改充值逻辑
- 不做 official-website 后台

## Allowed Files

### 后端

- `cloud-backend/app/api/v1/admin.py`
- `cloud-backend/app/schemas/admin.py`
- `cloud-backend/app/services/admin_service.py`（NEW）
- `cloud-backend/app/main.py`（仅当需要新增 router 注册，已有 admin router）
- `cloud-backend/tests/test_admin.py`（NEW 或扩展现有 admin 测试）

### 桌面端

- `desktop-app/src/pages/AdminPage.vue`（NEW）
- `desktop-app/src/services/cloudApi.ts`
- `desktop-app/src/router.ts`
- `desktop-app/src/components/dashboard/AppSidebar.vue`
- `desktop-app/src/stores/authStore.ts`

### 文档

- `docs/module-context/sprint-05-risk-02-basic-admin/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- 数据库 DDL / migrations
- `cloud-backend/app/models/**`
- `cloud-backend/app/providers/**`
- `cloud-backend/app/services/provider_service.py`
- `cloud-backend/app/services/credit_service.py`
- `cloud-backend/app/services/recharge_service.py`
- `cloud-backend/app/core/config.py`
- `desktop-app/src-tauri/**`
- `desktop-app/package.json` / `package-lock.json`
- `shared/**`
- `official-website/**`
- `.github/**`
- 任何真实密钥、证书、签名私钥、生产连接串

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 admin API 新增、后台权限边界和桌面端新页面。

必须暂停确认的情况：
- 需要新增或修改数据库 DDL / migrations
- 需要修改 Provider、Credit、Payment、Billing 模型或服务
- 需要在 allowed files 之外修改文件
- 需要新增依赖
- 发现 admin 查询可能泄露敏感数据（raw provider payload、用户密码 hash 等）

## Security Requirements

- 所有 `/api/v1/admin/*` 端点必须通过 `get_admin_user` 鉴权
- 非管理员请求返回 403（与现有 admin grant 端点一致）
- 不返回用户密码 hash、token、API key、raw provider response body
- 分页默认 limit ≤ 100，防止全量导出
- provider_call_log 不暴露 `raw_usage` 或 `raw_response`
- 管理员身份判断仅在服务端进行，不信任客户端角色声明

## Acceptance Criteria

- [ ] 5 个 admin 端点均可返回分页只读列表
- [ ] 非管理员调用任意 admin 端点返回 403
- [ ] 桌面端 AdminPage 可通过 `/admin` 路由访问
- [ ] AdminPage 5 个 tab 分别展示对应数据
- [ ] Sidebar 有"管理后台"入口
- [ ] 无权限时 AdminPage 显示"无管理权限"而非白屏
- [ ] 后端 admin focused tests 覆盖权限隔离 + 分页 + 数据正确性
- [ ] `npm run build` 通过
- [ ] `pytest tests/ -v` 通过
- [ ] `git diff --check` 通过
- [ ] `PROGRESS.md` 已追加记录

## Test Method

必须运行：

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/ -v
```

```powershell
cd ad-assistant/desktop-app
npm run build
```

```powershell
git diff --check
```

必须检查：

```powershell
git status --short --branch
```

## Rollback Plan

- revert 本任务 commit 移除 admin 端点和 AdminPage
- 如果只回退后端：移除 admin.py 中新增的 5 个 GET endpoint 路由注册
- 如果只回退前端：删除 AdminPage.vue 和路由/sidebar 注册
- 不涉及数据库迁移、用户数据或 Provider 状态

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 后端新增端点列表
- 桌面端 AdminPage 结构
- 权限模型说明
- 测试结果
- 安全自查（是否暴露敏感字段）
- 未实现内容
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
