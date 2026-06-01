# 27 Membership / Recharge Rebuild Guide

## Purpose

This document replaces the current S04-T04 implementation plan for the membership, package, recharge, and admin credit grant module.

CC must rebuild the module according to this document before commit, PR, or merge. The current implementation may be reused only after each rule below is satisfied.

## Why Rebuild

The module touches high-risk boundaries:

- database schema and migrations
- API contract and shared DTOs
- credit balance mutation and ledger writes
- payment / recharge flow
- admin-only credit grant
- plan and feature authorization

The module must therefore prefer correctness and auditability over quick UI completion.

## Non-Negotiable Rules

- The client must never decide the final plan, final credit grant, final payment status, provider cost, or billing result.
- No unlimited AI membership wording or behavior is allowed.
- Every balance mutation must be server-side, transactional, and have a matching `credit_ledger` row.
- Simulated payment is allowed only as an explicitly gated development/test mode.
- A normal logged-in user must not be able to grant themselves credits in production mode.
- Admin grant must validate both the caller and the target user.
- Recharge order, plan change, credit grant, and ledger write must be consistent in one transaction.
- If a credit mutation fails, the API must return a stable error response and must not leave partial business state.
- OpenAPI, shared DTOs, backend schemas, and frontend types must stay aligned.

## Allowed Scope

CC may modify only the files needed for this module:

- `cloud-backend/migrations/ddl/009_plans.sql`
- `cloud-backend/migrations/ddl/010_recharge_orders.sql`
- `cloud-backend/app/models/plan.py`
- `cloud-backend/app/models/recharge_order.py`
- `cloud-backend/app/models/__init__.py`
- `cloud-backend/app/services/plan_service.py`
- `cloud-backend/app/services/recharge_service.py`
- `cloud-backend/app/services/credit_service.py`
- `cloud-backend/app/api/v1/plans.py`
- `cloud-backend/app/api/v1/orders.py`
- `cloud-backend/app/api/v1/credits.py`
- `cloud-backend/app/api/v1/admin.py`
- `cloud-backend/app/api/deps.py`
- `cloud-backend/app/core/config.py`
- `cloud-backend/app/main.py`
- `cloud-backend/app/schemas/plan.py`
- `cloud-backend/app/schemas/recharge.py`
- `cloud-backend/app/schemas/admin.py`
- `cloud-backend/tests/test_plans.py`
- `cloud-backend/tests/test_recharge.py`
- `cloud-backend/tests/test_admin_grant.py`
- `cloud-backend/tests/test_credit_deduction.py`
- `cloud-backend/tests/test_migrations_integration.py`
- `desktop-app/src/pages/MembershipPage.vue`
- `desktop-app/src/components/dashboard/AppSidebar.vue`
- `desktop-app/src/router.ts`
- `desktop-app/src/services/cloudApi.ts`
- `shared/dto/plans.ts`
- `shared/dto/recharge.ts`
- `shared/openapi/plans.yaml`
- `shared/openapi/recharge.yaml`
- `tasks/current-task.md`
- `PROGRESS.md`

Do not modify Tauri permissions, local OCR service files, package files, lockfiles, provider routing, auth token storage, or unrelated UI pages in this task.

## Business Model

The project uses:

- monthly or yearly packages
- monthly included AI credits
- extra credit purchase

The project does not use:

- buyout / lifetime unlimited access
- unlimited AI membership
- client-side billing decisions
- client-side credit deduction

Initial visible packages:

- `standard`: 359 CNY/month
- `expert`: 559 CNY/month
- `enterprise`: 999 CNY/month

Credit amounts and final package benefits may be seed data, but wording must not claim unlimited AI usage.

## Database Design

### `plans`

Purpose: available package definitions.

Required columns:

- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `name VARCHAR(100) NOT NULL`
- `code VARCHAR(50) NOT NULL UNIQUE`
- `price_cny INTEGER NOT NULL`
- `monthly_credits INTEGER NOT NULL DEFAULT 0`
- `features_json TEXT`
- `sort_order INTEGER NOT NULL DEFAULT 0`
- `status VARCHAR(20) NOT NULL DEFAULT 'active'`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

Required constraints:

- `price_cny >= 0`
- `monthly_credits >= 0`
- `status IN ('active', 'inactive')`
- unique `code`

Seed rules:

- seed exactly `standard`, `expert`, `enterprise`
- no wording like `unlimited`, `无限制`, `不限量`, `无限 AI`
- features may describe supported tools, service level, monthly credits, and support level

### `recharge_orders`

Purpose: auditable order records for package purchases and extra credit purchase.

Required columns:

- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `user_id UUID NOT NULL REFERENCES users(id)`
- `plan_code VARCHAR(50)`
- `amount_cny INTEGER NOT NULL`
- `credits INTEGER NOT NULL`
- `payment_method VARCHAR(50) NOT NULL`
- `status VARCHAR(20) NOT NULL`
- `description TEXT`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `completed_at TIMESTAMPTZ`

Required constraints:

- `amount_cny > 0`
- `credits > 0`
- `payment_method IN ('simulated', 'alipay', 'wechat_pay', 'stripe', 'manual', 'offline')`
- `status IN ('pending', 'completed', 'cancelled', 'refunded')`

Index requirements:

- `user_id`
- `created_at DESC`
- `status`
- `plan_code`

### Migration Tests

`tests/test_migrations_integration.py` must include both new tables:

- table existence
- required columns
- important constraints
- basic insert/select path
- invalid status / invalid amount constraint checks

## Configuration

Add explicit config:

- `ENABLE_SIMULATED_PAYMENT: bool = False`
- `ADMIN_USER_IDS: list[str] = []`

Rules:

- `ENABLE_SIMULATED_PAYMENT` defaults to `False`.
- Tests may monkeypatch it to `True`.
- Local development may enable it in `.env`.
- Production-like default must not allow simulated recharge completion.
- `ADMIN_USER_IDS` controls who may call admin grant endpoints.

## Backend Service Design

### `grant_credits`

`grant_credits()` may exist in `credit_service.py`, but it must be transaction-safe and ledger-safe.

Required behavior:

- reject `amount <= 0`
- get or create the user's `credit_accounts` row
- update balance server-side
- write one `credit_ledger` row with `change_type='grant'`
- return the new balance
- never accept client-provided `balance_after`

Recommended implementation:

- use a transaction owned by the API/service caller
- use row lock or deterministic single-row update
- keep account and ledger consistent

### `deduct_credits`

Existing `deduct_credits()` must be fixed if this task touches credit mutation.

Required behavior:

- no negative final balance under concurrent calls
- no "provider succeeded but deduction silently failed" path
- if insufficient balance, return a controlled error or deduct exactly the allowed amount only when explicitly designed

Acceptable approaches:

- `SELECT ... FOR UPDATE` on the `credit_accounts` row before computing deduction
- or conditional `UPDATE credit_accounts SET balance = balance - :amount WHERE id = :id AND balance >= :amount RETURNING balance`

Add a concurrency-oriented test. SQLite cannot prove PostgreSQL row-lock behavior, so add the strongest practical unit test plus PostgreSQL integration coverage where possible.

### `create_recharge_order`

This is the core business function.

Inputs:

- `db`
- `user_id`
- `plan_code`
- `amount_cny`
- `payment_method`

Rules:

- either `plan_code` or `amount_cny` may be provided, but not both unless explicitly documented
- `plan_code` must refer to an active plan
- custom `amount_cny` must be allowed only if extra credit purchase is in scope
- simulated payment must require `settings.ENABLE_SIMULATED_PAYMENT is True`
- when simulated payment is disabled, create a `pending` order and do not grant credits
- when simulated payment is enabled, create a `completed` order and grant credits in the same transaction
- when buying a package, update both `users.plan_code` and `credit_accounts.plan_code` in the same transaction
- order creation, plan update, credit grant, and ledger write must commit or roll back together

Return shape:

- `order_id`
- `plan_code`
- `amount_cny`
- `credits`
- `new_balance`
- `status`
- `payment_method`
- `plan_changed`

## API Design

### `GET /api/v1/plans`

Auth:

- public is acceptable if only active package metadata is returned

Response:

- unified response envelope
- list active plans sorted by `sort_order`
- no internal IDs required unless needed by UI
- no unlimited wording

### `POST /api/v1/credits/recharge`

Auth:

- requires `get_current_user_with_device`

Request:

- `plan_code?: string`
- `amount_cny?: number`

Rules:

- default production behavior must not directly grant credits through simulated payment
- if `ENABLE_SIMULATED_PAYMENT=False`, return `pending` order or `403/409` with a clear error depending on chosen design
- if `ENABLE_SIMULATED_PAYMENT=True`, complete immediately for local/dev tests
- client must not submit `credits`, `status`, `payment_method`, `new_balance`, `user_id`, or `plan_changed`

Errors:

- invalid plan: `400 VALIDATION_ERROR`
- missing input: `400 VALIDATION_ERROR`
- simulated disabled: stable error code such as `SIMULATED_PAYMENT_DISABLED`, unless returning pending order
- unauthorized: existing auth error

### `GET /api/v1/orders`

Auth:

- requires `get_current_user_with_device`

Rules:

- user can only see their own orders
- pagination with bounded `limit`
- response must not expose other users' data

### `POST /api/v1/admin/credits/grant`

Auth:

- requires `get_admin_user`
- `get_admin_user` uses `ADMIN_USER_IDS`

Request:

- `user_id`
- `amount`
- `description`

Rules:

- caller must be in `ADMIN_USER_IDS`
- target `user_id` must be valid UUID
- target user must exist
- target user must be active unless explicitly documented otherwise
- grant must write `credit_ledger`
- response must not leak sensitive user data

Errors:

- admin not configured: `403 FORBIDDEN`
- caller not admin: `403 FORBIDDEN`
- invalid target UUID: `400 VALIDATION_ERROR`
- target user not found: `404 USER_NOT_FOUND`
- invalid amount: `400 VALIDATION_ERROR`

## Frontend Design

`MembershipPage.vue` is presentation and workflow only. It must not make billing decisions.

Required UI:

- current plan
- current credit balance
- package comparison
- recharge / upgrade confirmation
- order history
- clear message when payment is simulated or pending

Rules:

- do not claim payment succeeded unless backend returns `status='completed'`
- do not claim plan upgraded unless backend returns `plan_changed=true` or refreshed user state confirms it
- after successful package purchase, refresh balance, orders, and current user/plan state
- display pending order clearly when simulated payment is disabled
- do not expose admin grant UI in this task

## Shared DTO / OpenAPI Requirements

Update both:

- `shared/dto/plans.ts`
- `shared/dto/recharge.ts`
- `shared/openapi/plans.yaml`
- `shared/openapi/recharge.yaml`

They must match backend schemas exactly:

- request fields
- response fields
- error shapes
- auth requirements
- pending vs completed behavior

## Required Tests

### Backend Focused Tests

Plans:

- returns exactly active plans
- inactive plans are hidden
- sort order is stable
- no unlimited wording in seed features

Recharge:

- valid package purchase with simulated enabled creates completed order, grants credits, writes ledger, updates `users.plan_code`, updates `credit_accounts.plan_code`
- valid package purchase with simulated disabled does not grant credits
- invalid plan returns 400
- missing input returns 400
- client cannot submit final credits/status/payment result
- order history is user-scoped
- custom amount behavior is tested if kept in scope

Admin grant:

- non-admin gets 403
- empty `ADMIN_USER_IDS` gets 403
- admin can grant to existing active user
- invalid target UUID gets 400
- nonexistent target user gets 404
- grant writes ledger with `source_type='manual'`

Credit mutation:

- `grant_credits()` rejects non-positive amount
- `grant_credits()` writes balance and ledger consistently
- `deduct_credits()` cannot create negative balance
- concurrent or repeated deduction cannot bypass balance guard

Migration:

- `plans` and `recharge_orders` exist in PostgreSQL migration integration test
- constraints reject invalid status and invalid amounts
- seed data inserts cleanly

### Frontend Tests / Build

At minimum:

- `npm run build`
- TypeScript compile passes
- UI handles `completed`, `pending`, and error response states

## Required Verification Commands

Run from `cloud-backend`:

```powershell
python -m pytest tests/test_plans.py tests/test_recharge.py tests/test_admin_grant.py tests/test_credit_deduction.py -v -x
python -m pytest tests/test_migrations_integration.py -v -x
python -m pytest tests/ -v -x
```

Run from `desktop-app`:

```powershell
npm.cmd run build
```

Run from repo root:

```powershell
git diff --check
git status --short --branch
git diff --cached --name-status
```

## Reviewer-mode Checklist

Before commit, CC must run reviewer-mode and answer:

- Can a normal logged-in user grant themselves credits without a real or explicitly simulated payment gate?
- Does package purchase actually update backend plan authorization?
- Can admin grant target a nonexistent user?
- Can concurrent credit deduction create a negative balance or ledger mismatch?
- Are all credit mutations matched by `credit_ledger`?
- Do OpenAPI and shared DTO match backend schemas?
- Does PostgreSQL migration coverage include the new tables?
- Does the UI display pending vs completed payment honestly?
- Is there any unlimited AI wording?
- Is the staged file list limited to this task?

If any answer is unsafe, the task is not complete.

## Completion Output Required

CC must report:

- files changed
- exact business behavior implemented
- simulated payment behavior and config default
- admin grant authorization behavior
- plan update behavior
- credit mutation transaction strategy
- tests run with exact results
- reviewer-mode findings and fixes
- residual risks
- rollback plan
- `git status --short --branch`
- `git diff --cached --name-status`

