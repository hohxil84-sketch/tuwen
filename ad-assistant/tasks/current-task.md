# S05-R03: RBAC 角色权限最小体系

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-03-rbac`

## 背景

当前 RBAC 基础设施已完整：`ROLE_PERMISSIONS` dict、`PermissionChecker` class、User.role 字段、admin 端点全部使用 PermissionChecker。30 个 RBAC 测试通过。

残留问题：
- 废弃的 `get_admin_user` 函数仍存在于 deps.py（未被任何端点引用）
- `admin_service.py` 注释仍引用 `get_admin_user`
- 缺少角色越权防护测试（auth 端点不应允许客户端设置 role）
- 安全文档未覆盖 RBAC

## 用户目标

清理 RBAC 遗留代码、加固角色越权防护、补充安全文档，完成 RBAC 体系 formal signoff。

## What To Build

### 1. 清理废弃代码

- 移除 `deps.py` 中未使用的 `get_admin_user` 函数
- 修正 `admin_service.py` 注释（`get_admin_user` → `PermissionChecker`）

### 2. 角色越权防护

- Auth 端点（login/refresh）不返回 `role` 字段（当前已不返回，验证并补充测试）
- 测试确认普通用户无法通过任何 API 提升角色

### 3. 测试

- 新增 `TestDefaultDeny` class：无角色用户 → 403
- 新增 `TestRoleNotLeaked` test：auth 响应不含 role

### 4. 安全文档

- 更新 `docs/08-security-and-anti-crack.md`：新增 RBAC 小节

## What Not To Build

- 不做完整企业级组织架构
- 不做多租户
- 不做后台角色编辑 UI（S05-R02 已有 admin page）
- 不改真实支付或 Provider 路由

## Allowed Files

- `cloud-backend/app/api/deps.py`
- `cloud-backend/app/services/admin_service.py`
- `cloud-backend/tests/test_admin.py`
- `docs/08-security-and-anti-crack.md`
- `docs/module-context/sprint-05-risk-03-rbac/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- desktop UI
- Provider 实现和路由
- Payment/真实支付代码
- Tauri permissions
- CI / deployment

## Acceptance Criteria

- [ ] `get_admin_user` 废弃函数已移除
- [ ] 所有 admin 端点仅通过 PermissionChecker 鉴权
- [ ] Auth 端点不泄露 role 字段
- [ ] 测试覆盖 default-deny + role 未泄露
- [ ] `python -m pytest tests/ -v` 通过
- [ ] `git diff --check` 通过

## Test Method

```bash
cd ad-assistant/cloud-backend
python -m pytest tests/test_admin.py -v
python -m pytest tests/ -v
git diff --check
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 auth/permission 模型。

## Security Requirements

- 默认拒绝
- 权限检查在服务端执行
- 不信任客户端角色字段

## Rollback Plan

- revert commit
