# S05-R02: 基础后台最小可用管理台

## 背景

P0 MVP 包含基础后台。S05-R02 提供最小可用的管理数据面板。

管理员通过桌面端侧边栏「管理后台」入口访问只读数据面板，查看用户、订单、积分账户、Provider 调用日志和使用事件。

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `desktop-app/src/pages/AdminPage.vue` | users tab 新增 `role` 列 |
| `docs/module-context/sprint-05-risk-02-basic-admin/context.md` | **NEW** |
| `PROGRESS.md` | 进度记录 |
| `tasks/current-task.md` | 状态更新 |

### 未修改（已完整，无需变更）

- `cloud-backend/app/api/v1/admin.py` — 8 端点
- `cloud-backend/app/services/admin_service.py` — 6 查询函数
- `cloud-backend/app/schemas/admin.py` — 全部 DTO
- `cloud-backend/app/api/deps.py` — PermissionChecker
- `cloud-backend/tests/test_admin.py` + `test_admin_grant.py` — 30 tests
- `desktop-app/src/services/cloudApi.ts` — 5 admin API 函数

## 后端 API

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/admin/users` | `users:read` | 列出所有用户（分页） |
| GET | `/api/v1/admin/orders` | `orders:read` | 列出所有充值订单（分页） |
| GET | `/api/v1/admin/credit-accounts` | `users:read` | 列出所有积分账户（分页） |
| GET | `/api/v1/admin/provider-logs` | `provider_logs:read` | 列出所有 Provider 调用日志（分页） |
| GET | `/api/v1/admin/usage-events` | `usage_events:read` | 列出所有使用事件（分页） |
| POST | `/api/v1/admin/credits/grant` | `credits:grant` | 管理员手动发放积分 |
| POST | `/api/v1/admin/monthly-grant/run` | `credits:grant` | 手动触发月度积分发放 |
| GET | `/api/v1/admin/provider-health` | `provider_logs:read` | 熔断器状态查询 |

## 权限模型

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
}
```

- `role="user"` → 拒绝所有 admin 权限
- `ADMIN_USER_IDS` bootstrap fallback

鉴权链：`get_current_user` → `PermissionChecker(permission)` → role check → ADMIN_USER_IDS fallback → 403

## 前端 AdminPage

5 个 tab 视图：

| Tab | 展示字段 |
|-----|---------|
| 用户 | account, role, plan_code, status, created_at |
| 订单 | user_id, plan_code, amount_cny, credits, status, created_at |
| 积分账户 | user_id, plan_code, balance, monthly_grant, status |
| Provider 日志 | user_id, provider, model, feature, status, credits_charged, created_at |
| 使用事件 | user_id, event_type, feature, created_at |

- 分页：每页 20 条
- 错误处理：403 → 无权限提示

## 未实现

- 无增删改操作（grant 除外）
- 无搜索/筛选/排序/导出
- provider-health / monthly-grant 有 API 无 UI

## 安全

- 所有端点鉴权
- API 不暴露 password_hash
- Provider log 不暴露 raw payload

## 测试

```bash
python -m pytest tests/test_admin.py tests/test_admin_grant.py -v  # 30 passed
npm run build  # 77 modules, 0 errors
```

## 残余风险

- 若无 admin/operator 角色用户且 ADMIN_USER_IDS 为空，无人可访问后台
