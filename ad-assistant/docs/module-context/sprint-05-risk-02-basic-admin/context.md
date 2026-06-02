# S05-R02: 基础后台最小可用管理台 — 模块上下文

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 日期

2026-06-02

## 分支

`feature/sprint-05-risk-02-basic-admin`

## 方案说明

### 问题

P0 MVP 包含"基础后台"，但当前仅有一个 `POST /api/v1/admin/credits/grant` 端点。用户、订单、积分、Provider 日志、使用事件均无管理界面。

### 方案

新增 5 个只读 admin GET 端点 + 桌面端 AdminPage 5 tab 页签。复用现有 `get_admin_user` 权限依赖和 `ADMIN_USER_IDS` 白名单。

## 后端端点

| 端点 | 数据来源 | 分页 | 排除字段 |
|------|---------|------|---------|
| `GET /api/v1/admin/users` | users 表 | ✅ limit/offset | password_hash |
| `GET /api/v1/admin/orders` | recharge_orders 表 | ✅ | — |
| `GET /api/v1/admin/credit-accounts` | credit_accounts 表 | ✅ | — |
| `GET /api/v1/admin/provider-logs` | provider_call_log 表 | ✅ | raw_usage, raw_response |
| `GET /api/v1/admin/usage-events` | usage_events 表 | ✅ | metadata_json |

- 默认 limit=20，最大 100
- 所有端点需 `get_admin_user` 依赖（检查 user_id ∈ ADMIN_USER_IDS）
- 返回格式：`{success, data: {items, total, limit, offset}, error, request_id}`

## 权限模型

- **服务端鉴权**：复用 `app.api.deps.get_admin_user`
  - ADMIN_USER_IDS 为空 → 所有用户 403
  - user_id ∉ ADMIN_USER_IDS → 403
- **前端不预知角色**：Sidebar 始终显示"管理后台"入口
  - admin API 返回 200 → 正常展示数据
  - admin API 返回 403 → AdminPage 显示"无管理权限"
  - admin API 返回 401 → 显示登录提示（cloudApi.ts request() 行为）

## 桌面端结构

### AdminPage.vue

- 5 个 tab 页签：用户 / 订单 / 积分账户 / Provider 日志 / 使用事件
- 每个 tab 内：表格 + 上一页/下一页
- 状态处理：loading（"加载中..."）/ error（红色提示）/ forbidden（"无管理权限"）/ empty（"暂无数据"）
- cell 值 > 40 字符自动截断
- null/undefined → "—"

### Router

- `/admin` → AdminPage.vue（懒加载）

### Sidebar

- "系统设置" 组新增"管理后台"入口（🛡️ 图标）

## 修改文件清单

### 后端

| 文件 | 状态 | 说明 |
|------|------|------|
| `cloud-backend/app/schemas/admin.py` | 修改 | 新增 PaginatedItems + 5 个 Item schema |
| `cloud-backend/app/services/admin_service.py` | 新建 | 5 个查询方法 + _paginate helper |
| `cloud-backend/app/api/v1/admin.py` | 修改 | 新增 5 个 GET endpoint + _build_paginated |
| `cloud-backend/tests/test_admin.py` | 新建 | 12 tests（权限隔离 + 分页 + 敏感字段验证） |

### 桌面端

| 文件 | 状态 | 说明 |
|------|------|------|
| `desktop-app/src/services/cloudApi.ts` | 修改 | 新增 Admin DTO types + 5 个 API 函数 |
| `desktop-app/src/pages/AdminPage.vue` | 新建 | AdminPage 组件 |
| `desktop-app/src/router.ts` | 修改 | +1 route `/admin` |
| `desktop-app/src/components/dashboard/AppSidebar.vue` | 修改 | +1 nav item |

### 未修改

- `desktop-app/src/stores/authStore.ts`：未修改（AdminPage 直接调用 cloudApi.ts，权限由服务端判断）
- 数据库 DDL / migrations：未修改
- Provider、Credit、Payment 服务：未修改
- `cloud-backend/app/core/config.py`：未修改
- Tauri 权限、依赖、CI：未修改

## 验证结果

| 测试 | 命令 | 结果 |
|------|------|------|
| 后端 admin focused | `pytest tests/test_admin.py -v` | 12 passed |
| 后端全量回归 | `pytest tests/ -v` | 305 passed, 74 skipped |
| 前端构建 + 类型检查 | `npm run build` | 77 modules, 0 errors |
| 空白检查 | `git diff --check` | 通过 |

## 残余风险

- **手动 GUI 验证未执行**：AdminPage 需后端 + admin 用户才能完整验证（tab 切换、分页、403 处理、空数据状态）
- **无 RBAC**：仍依赖 ADMIN_USER_IDS 白名单（S05-R03 将替换）
- **仅只读**：无增删改操作、无筛选搜索、无排序、无导出
- **无统计图表**：纯表格展示，无 dashboard 摘要
- **authStore.ts 未添加 isAdmin computed**：前端不知道管理员身份，通过试探 API 判断（403 → 显示无权限），有额外 HTTP 请求开销

## 回滚方式

- revert 对应 commit
- 后端回退：移除 admin.py 中新增的 5 个 GET endpoint，删除 admin_service.py
- 前端回退：删除 AdminPage.vue，移除 router 和 sidebar 中的 admin 注册
- 不影响数据库、用户数据、Provider 状态

## 扩展点

- **筛选/搜索**：在 query params 中添加 `user_id`、`status`、`feature` 等 filter 参数
- **排序**：支持 `order_by` + `order_dir` query params
- **导出**：CSV/Excel 导出按钮
- **详情弹窗**：点击行展开详情
- **统计卡片**：顶部统计卡片（总用户数、今日调用量、本月收入等）

## 相关文档

- [S04-T04 会员/套餐/充值](../../27-membership-recharge-rebuild-guide.md) — admin grant 来源
- [residual-risk-tasks.md](../../../tasks/residual-risk-tasks.md) — 候选任务来源
- [S05-R03 RBAC 权限体系](../../../tasks/residual-risk-tasks.md#s05-r03-rbac-角色权限最小体系) — 下一任务

## 自审清单

- [x] 是否只实现了 tasks/current-task.md：是
- [x] 是否任务单由用户确认：是
- [x] 是否只修改了 allowed files：是（未修改 models、config、deps）
- [x] 是否没有混入无关文件：是
- [x] 是否没有新增未授权依赖：是
- [x] 是否没有触碰未确认的高风险边界：是
- [x] 是否没有 secrets、真实密钥、Token 或生产连接串：是
- [x] 是否完成任务单要求的测试：是
- [x] 是否更新模块上下文：是（本文档）
- [x] 是否列出未实现内容和残余风险：是
