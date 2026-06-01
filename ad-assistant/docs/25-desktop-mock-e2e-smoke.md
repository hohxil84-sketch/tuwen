# 25 — Desktop Mock AI E2E Smoke Verification Runbook

Date: 2026-06-01
Branch: `feature/sprint-02-task-06-desktop-mock-e2e-smoke`
Status: `VERIFIED` (API + Browser UI)

## Purpose

This runbook documents the exact commands and results for the mock MVP E2E
path:

```text
PostgreSQL/SQLite → Cloud Backend → Desktop Login → Mock AI Ad-Copy → Result Display
```

## Smoke Verification Results (2026-06-01)

### Environment

| Component | Detail |
|-----------|--------|
| OS | Windows 10 Pro |
| Python | 3.12.10 |
| Node.js | v24.16.0 |
| Docker | 29.4.3 |
| PostgreSQL | 16 (Docker container) |
| Backend database (smoke) | SQLite (see Note 1 below) |
| Desktop dev server | Vite 6.4.2 @ http://127.0.0.1:5173 |
| Cloud backend | uvicorn @ http://127.0.0.1:8000 |

### Note 1: SQLite for smoke test

PostgreSQL could not be used directly because the current SQLAlchemy models
use `DateTime` without `timezone=True` (→ `TIMESTAMP WITHOUT TIME ZONE`),
while `migrations/ddl/*.sql` creates `TIMESTAMPTZ` columns. The ORM sends
timezone-aware datetimes which asyncpg rejects. Tests pass because they use
SQLite in-memory (which is timezone-agnostic). For the smoke verification,
the backend was run with `DATABASE_URL=sqlite+aiosqlite:///dev.db`. This is
a pre-existing ORM/DDL mismatch to be resolved in a future task.

### API-Level Smoke Results

| Step | Description | Result | Evidence |
|------|-------------|--------|----------|
| 1 | Backend health check | ✅ PASS | `{"status":"ok","sprint":"01","mode":"auth-device"}` |
| 2 | Login (valid credentials) | ✅ PASS | Returns access_token, refresh_token, user={account:"test@example.com", plan_code:"standard"}, device={status:"active", is_new:false} |
| 3 | Mock AI ad-copy (with token) | ✅ PASS | Returns provider="mock", model="mock-text-v1", credits_charged=0, estimated_cost=0.01455, request_id="req_..." |
| 4 | Mock AI ad-copy (Chinese) | ✅ PASS | Same fields, Chinese product_name/selling_points accepted |
| 5 | provider_call_log written | ✅ PASS | Row recorded: provider=mock, model=mock-text-v1, status=success, credits_charged=0 |
| 6 | Logout | ✅ PASS | Refresh token revoked successfully |
| 7 | Token reuse after logout | ✅ PASS | Returns TOKEN_REUSE (security detection) |
| 8 | No-auth request | ✅ PASS | Returns HTTP 401 |
| 9 | Desktop dev server | ✅ PASS | Vite serves index.html + modules @ http://127.0.0.1:5173 |

### UI-Level Smoke Results (2026-06-01, live browser)

| Step | Description | Result | Evidence |
|------|-------------|--------|----------|
| 10 | Browser login form | ✅ PASS | Login form with account/password/device_fingerprint fields visible; login succeeds → redirect to /ocr |
| 11 | Mock AI panel visibility (after login) | ✅ PASS | "Mock AI 广告文案生成（仅 Mock）" panel visible with product_name, selling_points, platform, tone inputs |
| 12 | Generate mock ad-copy | ✅ PASS | Result card displays: provider=mock, model=mock-text-v1, 扣点=0, request_id=req_27a7a33502cb |
| 13 | Page refresh clears tokens | ✅ PASS | F5 refresh → login state cleared, Mock AI panel hidden, login prompt shown |
| 14 | OCR upload UI | ✅ PASS | Image upload/拖拽 area visible; recognition blocked (local PaddleOCR not started, out of scope) |

### Vite Proxy Configuration

The desktop dev server must proxy `/api` requests to the cloud backend to avoid
CORS errors. The proxy is configured in `vite.config.ts`:

```ts
server: {
  port: 5173,
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
    },
  },
},
```

The Vite dev server must also be started with `VITE_CLOUD_API_BASE_URL` pointing
to the Vite dev server itself (not the backend) so the browser sends same-origin
requests that the proxy forwards:

```bash
VITE_CLOUD_API_BASE_URL=http://127.0.0.1:5173 npm run dev
```

This ensures the browser sends requests to `http://127.0.0.1:5173/api/...`
(same-origin, no CORS) which Vite proxies to `http://127.0.0.1:8000`.

## Prerequisites

| Tool | Required | Check Command |
|------|----------|---------------|
| Docker | Yes (for PostgreSQL) | `docker --version` |
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

## Step 1 — Start PostgreSQL (Docker)

```bash
docker run -d --name pg-dev \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:16

until docker exec pg-dev pg_isready -U postgres; do sleep 1; done
docker exec pg-dev psql -U postgres -c "CREATE DATABASE ad_assistant_dev;"
```

**Tear down:** `docker rm -f pg-dev`

## Step 2 — Install Cloud Backend Dependencies

```bash
cd cloud-backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -e ".[dev]"
```

## Step 3 — Create Database And Seed Data (SQLite, Recommended)

Using SQLite avoids the pre-existing ORM/DDL DateTime mismatch:

```bash
cd cloud-backend
rm -f dev.db

# Create tables via SQLAlchemy
DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base
import app.models.user, app.models.device, app.models.auth_session
import app.models.risk_log, app.models.usage_event
import app.models.provider_call_log, app.models.credit_account, app.models.credit_ledger

async def init():
    e = create_async_engine('sqlite+aiosqlite:///dev.db')
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await e.dispose()
    print('Tables created')
asyncio.run(init())
"

# Seed test user + device
DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python scripts/dev_seed_user.py
```

### PostgreSQL Alternative (Blocked — DateTime Mismatch)

If using PostgreSQL, the DDL creates `TIMESTAMPTZ` columns but models use
`DateTime` → `TIMESTAMP WITHOUT TIME ZONE`. Workaround: use
`Base.metadata.create_all()` against PostgreSQL (creates matching columns),
but the backend ORM will still fail at runtime when it sends timezone-aware
datetimes. This needs a future fix.

## Step 4 — Start The Cloud Backend

```bash
cd cloud-backend
DATABASE_URL="sqlite+aiosqlite:///dev.db" \
JWT_SECRET_KEY="dev-secret-key-not-for-production" \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:
```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","sprint":"01","mode":"auth-device","request_id":"..."}
```

## Step 5 — Start The Desktop Dev Server

```bash
cd desktop-app
npm install    # one time
VITE_CLOUD_API_BASE_URL=http://127.0.0.1:5173 npm run dev    # → http://127.0.0.1:5173
```

**重要：** 必须设置 `VITE_CLOUD_API_BASE_URL` 指向 Vite dev server 自身，
让浏览器走同源 `/api` → Vite 代理 → 后端（`:8000`），避免跨域错误。
代理配置见 `vite.config.ts`。

The cloud API base URL defaults to `http://127.0.0.1:8000` when not overridden.
Override with `VITE_CLOUD_API_BASE_URL` in `desktop-app/.env` if needed.

## Step 6 — API Smoke Test (curl)

```bash
# Login
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account":"test@example.com","password":"correct-password","device_fingerprint":"device-fingerprint-abc"}'

# Expected: {"success":true,"data":{"access_token":"...","refresh_token":"...","user":{...},"device":{...}},...}

# Mock AI (save token first)
TOKEN="<access_token from login>"
curl -s -X POST http://127.0.0.1:8000/api/v1/mock-ai/ad-copy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"product_name":"TestProduct","selling_points":["fast","cheap","good"],"platform":"weixin","tone":"pro"}'

# Expected: {"success":true,"data":{"feature":"mock_ad_copy","provider":"mock","model":"mock-text-v1","credits_charged":0,...},"request_id":"req_..."}

# Logout
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token from login>"}'
```

For Chinese content, write the JSON body to a UTF-8 file and use `-d @file.json`.

## Step 7 — Browser Manual Smoke Checklist

Open `http://127.0.0.1:5173` in a browser.

| # | Action | Expected |
|---|--------|----------|
| 1 | Navigate to Login page | Login form visible |
| 2 | Enter credentials (see seed output) | — |
| 3 | Click login | Redirected to OCR page; account name in header |
| 4 | Check Mock AI panel | "Mock AI 广告文案生成（仅 Mock）" visible |
| 5 | Fill product info + click generate | Result card: provider=mock, model=mock-text-v1, credits_charged=0, request_id |
| 6 | Refresh page (F5) | Logged out; panel hidden; no tokens in storage |
| 7 | Try OCR upload | UI responds; recognition fails without local OCR service |

## Environment Variables Quick Reference

| Variable | Purpose | Dev Default |
|----------|---------|-------------|
| `DATABASE_URL` | DB connection string | `sqlite+aiosqlite:///dev.db` (smoke) |
| `JWT_SECRET_KEY` | HS256 signing key (MUST override default) | Set explicitly |
| `VITE_CLOUD_API_BASE_URL` | Desktop cloud API base URL. **Two paths:**<br>① API curl / direct backend requests: `http://127.0.0.1:8000`<br>② Browser UI smoke / Vite proxy path: **must** use `http://127.0.0.1:5173` so the browser sends same-origin requests to the Vite dev server, which proxies `/api` → backend `:8000` (avoids CORS) | `http://127.0.0.1:8000` (direct) / `http://127.0.0.1:5173` (proxy) |

## Known Issues

1. **DDL / ORM DateTime mismatch:** `migrations/ddl/*.sql` uses `TIMESTAMPTZ`
   but SQLAlchemy models use `DateTime` → `TIMESTAMP WITHOUT TIME ZONE`.
   Backend ORM writes fail against DDL-created PostgreSQL tables.
   Smoke test used SQLite as workaround. Should be resolved in future task.

2. **`datetime.utcnow()` deprecation:** Seed script uses deprecated method
   when running against PostgreSQL. Resolved together with issue #1.

3. **OCR requires local Python service:** PaddleOCR local service not in
   scope for this task. OCR upload/display UI stays intact.

4. **Chinese encoding in curl:** Windows/MinGW curl mishandles UTF-8 in
   `-d` string. Use `-d @file.json` with UTF-8 encoded file.

## Related Docs

- Desktop guide: `docs/09-desktop-app-guide.md`
- Cloud backend guide: `docs/11-cloud-backend-guide.md`
- Mock AI API docs: `docs/23-mock-ai-api-endpoint.md`
- Desktop mock client: `docs/24-desktop-mock-ai-api-client.md`
- Seed script: `cloud-backend/scripts/dev_seed_user.py`
