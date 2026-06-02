# S05-R02: 基础后台最小可用管理台

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-02-basic-admin`

## 背景

P0 MVP 包含基础后台。当前已有 admin API（8 端点）、admin service、AdminPage.vue（5 tab）和 30 个测试。本任务对已有系统进行审计、补充列展示、文档和 formal signoff。

## 用户目标

确认管理员可访问只读数据面板，所有关键实体可查看，非管理员被拒绝。

## What To Build

### 1. 审计已有 Admin 系统

- Backend: `admin.py` API（8 端点）、`admin_service.py`、`admin.py` schemas → 已完整
- Frontend: `AdminPage.vue`（5 tab + 分页）、`cloudApi.ts`（5 admin 函数）→ 基本完整
- Auth: `PermissionChecker`（role-based + ADMIN_USER_IDS fallback）→ 已完整
- Tests: `test_admin.py` + `test_admin_grant.py`（30 tests）→ 已完整

### 2. 补充缺失列

- AdminPage.vue users tab 已有 `account, plan_code, status, created_at`，但 API 返回的 `role` 未展示
- 在 users tab 的 columns 中添加 `role` 列

### 3. 文档

- 新增模块上下文 `docs/module-context/sprint-05-risk-02-basic-admin/context.md`
- 更新 `PROGRESS.md`

## What Not To Build

- 不做复杂 RBAC（S05-R03 专项）
- 不做增删改操作（仅只读展示）
- 不修改数据库
- 不新增 API 端点

## Allowed Files

- `desktop-app/src/pages/AdminPage.vue`
- `docs/module-context/sprint-05-risk-02-basic-admin/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- `cloud-backend/**`（已有代码不需要修改）
- 数据库 DDL / migrations
- Provider 路由和真实 AI 调用代码
- Tauri permissions
- CI / deployment

## Acceptance Criteria

- [ ] AdminPage users tab 展示 `role` 列
- [ ] `npm run build` 通过
- [ ] `python -m pytest tests/test_admin.py tests/test_admin_grant.py -v` 通过
- [ ] `git diff --check` 通过

## Test Method

```bash
cd ad-assistant/cloud-backend
python -m pytest tests/test_admin.py tests/test_admin_grant.py -v

cd ad-assistant/desktop-app
npm run build

git diff --check
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 admin API 和后台权限边界。

## Security Requirements

- 不修改鉴权逻辑
- 不暴露 password_hash
- 不暴露 token、密钥

## Rollback Plan

- revert commit

## Completion Output Required

- 后台范围、权限模型、接口列表、测试结果、安全自查、风险、中文 commit message、PR 摘要
