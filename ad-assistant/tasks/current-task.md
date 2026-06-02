# S05-R03: RBAC 角色权限最小体系

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-03-rbac`

## 完成摘要

- User 模型新增 `role` 列（VARCHAR(20)，默认 `"user"`）
- 新增 `ROLE_PERMISSIONS` 角色权限映射 + `PermissionChecker` 依赖类（`deps.py`）
- 6 个 admin 端点全部从 `Depends(get_admin_user)` 替换为 `Depends(PermissionChecker("..."))` 细粒度权限
- 角色体系：admin（全部 5 权限）、operator（4 读权限，不可授权积分）、user（无权限）
- `ADMIN_USER_IDS` 保留为 bootstrap 回退机制
- `AdminUserItem` schema 新增 `role` 字段
- 迁移 SQL（001_add_user_role.sql）+ 回滚 SQL（001_rollback.sql）
- test_admin.py 从 12 扩展到 23 tests：admin role / operator role / forbidden / bootstrap fallback
- 全量测试：316 passed, 74 skipped
- 未修改桌面端、services、config、第三方依赖

## 背景

当前管理员能力依赖 `ADMIN_USER_IDS` 硬编码白名单（[config.py](ad-assistant/cloud-backend/app/core/config.py) `ADMIN_USER_IDS: list[str] = []`），[deps.py](ad-assistant/cloud-backend/app/api/deps.py) 的 `get_admin_user` 只检查 `str(user.id) in settings.ADMIN_USER_IDS`。该方式可用于 MVP 早期，但无法表达角色、权限层级、审计或后续后台管理扩展。

User 模型当前字段：`id`, `account`, `password_hash`, `plan_code`, `status`, `created_at`, `updated_at` — 无角色字段。

## 用户目标

建立最小 RBAC，使后台和管理员能力从硬编码白名单过渡到可审计、可扩展的角色权限模型。

## What To Build

### 1. User 模型 — 新增 role 列

- `User` 表新增 `role` 列：`Mapped[str]`, default `"user"`, server_default `"'user'"`, `String(20)`
- 合法角色值：`"admin"`, `"operator"`, `"user"`
- 向后兼容：现有用户 role 默认为 `"user"`，首次启动后可通过 SQL 手动提升角色

### 2. 权限定义与 PermissionChecker

新增 `PermissionChecker` 类（在 `deps.py` 中）：

```python
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"users:read", "orders:read", "credits:grant", "provider_logs:read", "usage_events:read"},
    "operator": {"users:read", "orders:read", "provider_logs:read", "usage_events:read"},
    # "user" has no admin permissions (default deny)
}

class PermissionChecker:
    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, user: Annotated[User, Depends(get_current_user)]) -> User:
        ...
```

- 检查 `user.role` → `ROLE_PERMISSIONS` 映射
- 向后兼容：如果 role 无权限但 `str(user.id) in settings.ADMIN_USER_IDS`，仍允许（bootstrap 回退）
- 未定义权限 → 默认拒绝
- `get_admin_user` 保留内部实现，改为调用 `PermissionChecker("admin")` 等效逻辑

### 3. 迁移 admin 端点权限

将 [admin.py](ad-assistant/cloud-backend/app/api/v1/admin.py) 中所有 `Depends(get_admin_user)` 替换为细粒度权限：

| 端点 | 新权限 |
|------|--------|
| `GET /users` | `users:read` |
| `GET /orders` | `orders:read` |
| `GET /credit-accounts` | `users:read` |
| `GET /provider-logs` | `provider_logs:read` |
| `GET /usage-events` | `usage_events:read` |
| `POST /credits/grant` | `credits:grant` |

### 4. AdminUserItem schema

- `AdminUserItem` 新增 `role: str` 字段，管理员可查看用户角色

### 5. 数据库迁移

- 新建 `cloud-backend/migrations/001_add_user_role.sql`：`ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';`
- 新建 `cloud-backend/migrations/001_rollback.sql`：`ALTER TABLE users DROP COLUMN IF EXISTS role;`

### 6. 测试

- 更新现有 `test_admin.py`：用 `user.role = "admin"` 替代 `ADMIN_USER_IDS` monkeypatch
- 新增参数化测试：
  - `operator` 可访问 4 个读端点但 POST `/credits/grant` 返回 403
  - `user` 角色所有 6 个端点返回 403
  - bootstrap 回退：`ADMIN_USER_IDS` 中包含 user_id 但 role 为 `"user"` 仍可访问
  - 未知权限代码默认拒绝

### 7. 文档

- 更新 `docs/08-security-and-anti-crack.md`：补充 RBAC 角色权限说明
- 新建 `docs/module-context/sprint-05-risk-03-rbac/context.md`

### 8. 进度记录

- 追加更新 `PROGRESS.md`

## What Not To Build

- 不做完整企业级组织架构（用户组、层级继承）
- 不做多租户
- 不做后台角色编辑 UI（管理端界面另起任务）
- 不改真实支付或 Provider 路由
- 不在桌面端做角色显示/编辑
- 不新增 SQLAlchemy 关联表（roles / user_roles / role_permissions 表）
- 不新增 FastAPI 依赖或第三方库

## Allowed Files

- `cloud-backend/app/models/user.py`
- `cloud-backend/app/api/deps.py`
- `cloud-backend/app/api/v1/admin.py`
- `cloud-backend/app/schemas/admin.py`
- `cloud-backend/app/core/config.py`（如需补充注释）
- `cloud-backend/tests/test_admin.py`
- `cloud-backend/migrations/001_add_user_role.sql`（NEW）
- `cloud-backend/migrations/001_rollback.sql`（NEW）
- `docs/08-security-and-anti-crack.md`
- `docs/module-context/sprint-05-risk-03-rbac/context.md`（NEW）
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- `desktop-app/**`（桌面端本次不涉及）
- `official-website/**`
- `shared/**`
- `cloud-backend/app/services/**`（服务层不变）
- `cloud-backend/app/models/` 除 `user.py` 外的所有 model
- `cloud-backend/app/providers/**`
- `.github/**`
- Payment / Credit / Provider 服务实现
- Tauri permissions
- CI / deployment

## Acceptance Criteria

- [ ] User 表新增 `role` 列，默认 `"user"`，合法值 admin/operator/user
- [ ] 管理员接口不再只依赖硬编码 `ADMIN_USER_IDS` 白名单
- [ ] `operator` 角色可查看用户/订单/日志但不可授权积分（`credits:grant` 返回 403）
- [ ] 普通用户（`user` 角色）所有管理端点返回 403
- [ ] `ADMIN_USER_IDS` 作为 bootstrap 回退机制仍有效
- [ ] 未定义权限默认拒绝（security-first）
- [ ] 权限检查完全在服务端执行
- [ ] `AdminUserItem` schema 包含 `role` 字段
- [ ] 迁移和回滚 SQL 脚本已提供
- [ ] 现有 12 个 admin 测试 + 新增测试全部通过
- [ ] `python -m pytest tests/ -v` 通过
- [ ] `git diff --check` 通过
- [ ] `PROGRESS.md` 已追加本任务记录

## Test Method

必须运行：

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/ -v
```

```powershell
git diff --check
```

必须检查：

```powershell
git status --short --branch
```

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 auth/permission 模型重构和数据库 schema 变更（User 表新增 role 列）。权限模型从硬编码白名单迁移到角色-权限映射。

必须暂停确认的情况：
- 需要新增第三方依赖
- 需要修改 forbidden files
- 需要新增/删除 API 端点（非权限替换）
- 测试失败无法在任务范围内修复
- 需要修改桌面端或前端代码

## Security Requirements

- 默认拒绝：未知权限代码、未知角色一律返回 403
- 权限检查必须在服务端执行
- 不信任客户端传入的角色字段
- `operator` 角色不可授权积分（最小权限原则）
- 迁移脚本只添加列不删除数据

## Rollback Plan

1. Revert 本任务 commit
2. 执行 `cloud-backend/migrations/001_rollback.sql` 删除 `role` 列
3. 恢复 `admin.py` 中所有 `Depends(get_admin_user)` 依赖
4. 恢复 `AdminUserItem` 删除 `role` 字段
5. 不影响用户数据、积分、订单或 Provider

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 权限模型设计说明
- 迁移策略和影响范围
- 测试命令和结果
- 未实现内容
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
