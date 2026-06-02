# S05-R03: RBAC 角色权限最小体系

## 背景

S05-R03 建立最小 RBAC 体系，使后台权限从硬编码白名单过渡到角色权限模型。

RBAC 基础设施在此前 S04 阶段已实现，本任务完成清理、加固和 formal signoff。

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `cloud-backend/app/api/deps.py` | 移除未使用的 `get_admin_user` 废弃函数（+ 注释说明） |
| `cloud-backend/app/services/admin_service.py` | 修正注释（`get_admin_user` → `PermissionChecker`） |
| `cloud-backend/tests/test_admin.py` | 新增 4 tests：default-deny（2）+ role 未泄露（2） |
| `docs/module-context/sprint-05-risk-03-rbac/context.md` | **NEW** |
| `PROGRESS.md` | 进度记录 |
| `tasks/current-task.md` | 状态更新 |

### 未修改（已有完整实现）

- `cloud-backend/app/api/deps.py`：`ROLE_PERMISSIONS` + `PermissionChecker`（保留不变）
- `cloud-backend/app/api/v1/admin.py`：8 端点全部使用 `PermissionChecker`
- `cloud-backend/app/schemas/auth.py`：`UserInfo` 不含 `role`（设计正确）
- `cloud-backend/app/models/user.py`：`role` 列（VARCHAR(20)，默认 `"user"`）
- `docs/08-security-and-anti-crack.md`：RBAC 小节（已存在）

## 权限模型

| 角色 | 权限 |
|------|------|
| `admin` | users:read, orders:read, credits:grant, provider_logs:read, usage_events:read |
| `operator` | users:read, orders:read, provider_logs:read, usage_events:read |
| `user` (default) | 无管理权限（默认拒绝） |

## 鉴权链

```
get_current_user → PermissionChecker("permission")
  ├── ROLE_PERMISSIONS[user.role] → check permission → allow
  ├── ADMIN_USER_IDS fallback → allow (bootstrap)
  └── default → 403 FORBIDDEN
```

## 安全特性

- 默认拒绝：未定义角色 → 空权限集 → 403
- 服务端鉴权：所有权限检查在 `PermissionChecker` 依赖中完成
- 不信任客户端：`role` 不出现在 login/refresh 响应中
- 永不泄露：`UserInfo` 只有 `id`, `account`, `plan_code`

## 测试

```bash
python -m pytest tests/test_admin.py -v  # 27 passed
python -m pytest tests/ -v               # 385 passed, 74 skipped
```

新增测试覆盖：
- `TestDefaultDeny`：未知角色 / user 角色 → 403
- `TestRoleNotLeaked`：auth 响应不含 role

## 残余风险

- `ADMIN_USER_IDS` bootstrap fallback 可绕过角色系统 — 用于首次管理员提升，应在生产环境中设为空
- 无角色编辑 UI（需数据库直连修改 `users.role`）
- 无审计日志记录角色变更
