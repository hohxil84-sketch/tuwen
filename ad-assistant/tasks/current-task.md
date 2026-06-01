# S04-T04: 会员/套餐/充值流程 (Membership / Package / Recharge)

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 分支

`feature/sprint-04-task-04-membership-recharge`

---

## 实现记录 (2026-06-02)

### 修改文件 (30 files)

**后端新增 (15 files)**
- `cloud-backend/migrations/ddl/009_plans.sql` — plans 表 DDL + 3 档套餐 seed data
- `cloud-backend/migrations/ddl/010_recharge_orders.sql` — recharge_orders 表 DDL
- `cloud-backend/app/models/plan.py` — Plan SQLAlchemy model
- `cloud-backend/app/models/recharge_order.py` — RechargeOrder SQLAlchemy model
- `cloud-backend/app/services/plan_service.py` — list_active_plans() + get_plan_by_code()
- `cloud-backend/app/services/recharge_service.py` — create_recharge_order() (订单 + grant)
- `cloud-backend/app/api/v1/plans.py` — GET /api/v1/plans（公开端点）
- `cloud-backend/app/api/v1/orders.py` — GET /api/v1/orders（登录）
- `cloud-backend/app/api/v1/admin.py` — POST /api/v1/admin/credits/grant（admin 白名单）
- `cloud-backend/app/schemas/plan.py` — PlanResponse, PlanListData
- `cloud-backend/app/schemas/recharge.py` — RechargeRequest/Response, OrderItem/ListData
- `cloud-backend/app/schemas/admin.py` — AdminGrantRequest/Response
- `cloud-backend/tests/test_plans.py` — 8 tests (plan listing + model)
- `cloud-backend/tests/test_recharge.py` — 15 tests (grant + recharge + orders API)
- `cloud-backend/tests/test_admin_grant.py` — 6 tests (admin auth + grant)

**后端修改 (6 files)**
- `cloud-backend/app/models/__init__.py` — export Plan, RechargeOrder
- `cloud-backend/app/services/credit_service.py` — + grant_credits() (atomic grant + ledger)
- `cloud-backend/app/api/v1/credits.py` — + POST /api/v1/credits/recharge
- `cloud-backend/app/api/deps.py` — + get_admin_user() dependency
- `cloud-backend/app/core/config.py` — + ADMIN_USER_IDS
- `cloud-backend/app/main.py` — register 3 new routers (admin, orders, plans)

**前端新增 (1 file)**
- `desktop-app/src/pages/MembershipPage.vue` — 当前套餐 banner + 3 列套餐对比 + 充值确认弹窗 + 充值记录表

**前端修改 (3 files)**
- `desktop-app/src/services/cloudApi.ts` — + listPlans(), rechargeCredits(), listOrders()
- `desktop-app/src/components/dashboard/AppSidebar.vue` — + "会员中心" 导航
- `desktop-app/src/router.ts` — + /membership 路由

**Shared 新增 (4 files)**
- `shared/dto/plans.ts`, `shared/dto/recharge.ts`
- `shared/openapi/plans.yaml`, `shared/openapi/recharge.yaml`

### 实现内容

全部按计划完成。核心设计：
- **grant_credits()** 参照 deduct_credits() 模式：atomic UPDATE balance + ledger write
- **recharge**: user 选套餐 → create_recharge_order() 创建订单 + grant_credits() 授予积分（simulated payment）
- **admin grant**: get_admin_user 检查 ADMIN_USER_IDS 白名单 → grant_credits(source_type="manual")
- **MembershipPage**: 深色主题，套餐对比卡片 + 确认弹窗 + 订单历史表

### 未实现内容

- 真实支付集成、月度自动发放调度器、套餐按比例退费、积分过期、年费定价、管理员 UI

### 自审结论

- 只实现了 tasks/current-task.md 允许的内容: 是
- 只修改了 allowed files: 是
- 未混入无关文件: 是
- 未新增依赖: 是
- 未触碰高风险边界（已声明）: 是（DDL + credit 已在任务单声明）
- 未存储 secrets: 是
- 测试覆盖: 29 个新测试全部通过
- 回归测试: 279 passed, 57 skipped
- 构建: npm run build 通过（68 modules, 0 errors）
- PROGRESS.md: 已更新

### 测试结果

```
# 新模块聚焦测试
python -m pytest tests/test_plans.py tests/test_recharge.py tests/test_admin_grant.py -v -x
29 passed

# 后端全量回归
python -m pytest tests/ -v
279 passed, 57 skipped

# 桌面端构建
npm run build
68 modules, 0 errors
```

### 是否触发高风险暂停规则

否 — DDL 和 credit 变更已在任务单中声明并获用户确认。

### 风险和回滚方式

1. **simulated 支付**: 无真实支付网关，充值即到账。未来接入真实支付时替换 payment_method 逻辑。
2. **admin 白名单**: 通过 config ADMIN_USER_IDS 控制，无 RBAC。未来可扩展为 role 表。
3. **月度发放未调度**: grant_credits() 函数可用，但无 cron 触发。需单独任务实现调度器。
4. **回滚方式**: revert 对应提交，删除 plans / recharge_orders 表。

## 背景

项目已有 credit 基础（账户、流水、扣费），但缺少套餐展示、充值购买、管理员赠送额度等业务流程。`docs/19-pricing-and-credit-system.md` 定义了 3 档套餐和月度额度发放规则，均未实现。

## 本次只开发什么

### Phase 1: Database
- `migrations/ddl/009_plans.sql` — plans 表 DDL + seed
- `migrations/ddl/010_recharge_orders.sql` — recharge_orders 表 DDL
- `app/models/plan.py` — Plan SQLAlchemy model
- `app/models/recharge_order.py` — RechargeOrder SQLAlchemy model

### Phase 2: Backend Services
- `credit_service.py` — 新增 `grant_credits()` (atomic grant + ledger)
- `plan_service.py` (NEW) — 套餐查询
- `recharge_service.py` (NEW) — 充值订单 + 积分授予

### Phase 3: Backend API
- `GET /api/v1/plans` (NEW) — 公开端点
- `POST /api/v1/credits/recharge` (MODIFY) — 用户充值
- `GET /api/v1/orders` (NEW) — 订单历史
- `POST /api/v1/admin/credits/grant` (NEW) — 管理员赠送
- `deps.py` — 新增 `get_admin_user` dependency

### Phase 4: Frontend
- `MembershipPage.vue` (NEW) — 套餐对比 + 充值 + 流水
- `AppSidebar.vue` — + "会员中心"
- `router.ts` — + `/membership`
- `cloudApi.ts` — + `listPlans()`, `rechargeCredits()`, `listOrders()`

### Phase 5: Schemas / DTOs / OpenAPI
- `schemas/plan.py`, `schemas/recharge.py`, `schemas/admin.py` (NEW)
- `shared/dto/plans.ts`, `shared/dto/recharge.ts` (NEW)
- `shared/openapi/plans.yaml`, `shared/openapi/recharge.yaml` (NEW)

## 本次不开发什么

- 真实支付集成 (Stripe/Alipay/WeChat Pay)
- 月度自动发放调度器 (cron/scheduler)
- 套餐中间切换按比例退费
- 积分过期逻辑 / 年费定价 / 发票/收据
- 管理员管理 UI

## 允许修改哪些文件

见上方各 Phase 列出的文件。禁止修改 `desktop-app/local-service/**`、`desktop-app/src-tauri/**`、`package.json`、`package-lock.json`。

## 验收标准

- [ ] Plans API 返回 3 档活跃套餐 (标准版/专家版/企业版)
- [ ] 用户可通过 recharge API 充值并获得积分 (atomic grant + ledger)
- [ ] 管理员可给指定用户赠送积分 (admin auth 白名单)
- [ ] MembershipPage 展示套餐对比 + 当前余额 + 充值按钮 + 流水
- [ ] 所有新测试通过 + 已有回归测试通过
- [ ] npm run build 通过

## 是否允许新增依赖

不允许。

## 是否涉及重大变更

**是** — 新增 2 张数据库表 (plans, recharge_orders)，新增 credit grant 操作（修改余额）。
