# S05-R03: RBAC 角色权限最小体系

## 背景

S04-T04 引入了 `get_admin_user` 依赖和 `ADMIN_USER_IDS` 硬编码白名单。S05-R02 在此基础上新增了 5 个只读管理端点，所有端点复用同一个 `get_admin_user` 检查。该方式无法区分不同级别的管理权限（如只读 vs 授权积分）。

S05-R03 将权限模型从硬编码白名单迁移到角色-权限映射，支持 `admin`（全部权限）和 `operator`（只读，不可授权积分）两个管理层级。

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `app/models/user.py` | 新增 `role` 列（VARCHAR(20)，默认 `"user"`） |
| `app/api/deps.py` | 新增 `ROLE_PERMISSIONS` 映射 + `PermissionChecker` 类；重构 `get_admin_user` |
| `app/api/v1/admin.py` | 6 个端点全部从 `Depends(get_admin_user)` 替换为 `Depends(PermissionChecker("..."))` |
| `app/schemas/admin.py` | `AdminUserItem` 新增 `role: str` 字段 |
| `tests/test_admin.py` | 完全重写（23 tests）：admin role / operator role / forbidden / bootstrap fallback |
| `docs/08-security-and-anti-crack.md` | 新增 RBAC 章节 |
| `migrations/001_add_user_role.sql` | 迁移 SQL |
| `migrations/001_rollback.sql` | 回滚 SQL |

### 未修改

- `desktop-app/**` — 桌面端 AdminPage 不感知角色（服务端权限判断，403 时显示无权限）
- `app/services/**` — 服务层不变
- 数据库其他表
- 第三方依赖

## 权限映射

```python
ROLE_PERMISSIONS = {
    "admin": {
        "users:read", "orders:read", "credits:grant",
        "provider_logs:read", "usage_events:read",
    },
    "operator": {
        "users:read", "orders:read",
        "provider_logs:read", "usage_events:read",
    },
    # "user" → empty set (deny all)
}
```

## 端点权限对应

| 端点 | 权限 | admin | operator | user |
|------|------|-------|----------|------|
| `GET /users` | `users:read` | ✅ | ✅ | ❌ |
| `GET /orders` | `orders:read` | ✅ | ✅ | ❌ |
| `GET /credit-accounts` | `users:read` | ✅ | ✅ | ❌ |
| `GET /provider-logs` | `provider_logs:read` | ✅ | ✅ | ❌ |
| `GET /usage-events` | `usage_events:read` | ✅ | ✅ | ❌ |
| `POST /credits/grant` | `credits:grant` | ✅ | ❌ | ❌ |

## Bootstrap / 向后兼容

`PermissionChecker` 检查顺序：
1. `user.role` → `ROLE_PERMISSIONS` 映射（主要路径）
2. `str(user.id) in settings.ADMIN_USER_IDS`（bootstrap 回退）

这保证：
- 现有通过 `ADMIN_USER_IDS` 配置的管理员不会因迁移而失去权限
- 首次部署时可以通过配置文件设置管理员，再通过 SQL 提升 role
- 最终可清空 `ADMIN_USER_IDS` 完全依赖 role

## 安全设计原则

- **默认拒绝**：未知角色返回空权限集；未知权限代码拒绝
- **服务端执行**：权限检查完全在 FastAPI 依赖层完成，不信任客户端
- **最小权限**：operator 不可授权积分
- **审计就绪**：`AdminUserItem` 包含 `role` 字段，管理员可审计用户角色分布

## 迁移方式

```bash
# 生产环境迁移
psql -d ad_assistant -f migrations/001_add_user_role.sql

# 提升第一个管理员
psql -d ad_assistant -c "UPDATE users SET role = 'admin' WHERE account = 'admin@example.com';"
```

## 测试

```bash
cd ad-assistant/cloud-backend
python -m pytest tests/test_admin.py -v  # 23 tests
python -m pytest tests/ -v                # 316 passed, 74 skipped
```

## 扩展点

- 新增角色：在 `ROLE_PERMISSIONS` 中增加条目（无需改模型）
- 新增权限：在对应 role 的 set 中添加权限代码 + 在端点使用 `PermissionChecker("new:perm")`
- 未来可引入 `roles`/`user_roles` 关联表和后台角色编辑 UI
- 未来可在 JWT payload 中嵌入角色信息减少 DB 查询

## 残余风险

- `users.role` 是单值字符串，不支持一个用户同时拥有多个角色（当前不需要）
- 没有角色变更审计日志（后续可通过 `risk_log` 或 admin audit log 补齐）
- 桌面端 AdminPage 仍通过 API 403 判断权限（未预先读取用户角色）
