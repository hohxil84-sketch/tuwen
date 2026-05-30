# Sprint-01 数据库迁移方案草案

> ⚠️ **草案 — 等待用户确认后执行。** 数据库结构一旦落地影响后续迁移，属于重大变更。

---

## 一、数据库选型（待确认）

| 选项 | 优势 | 建议 |
|------|------|------|
| PostgreSQL | JSONB、并发强、开源协议宽松 | 推荐 |
| MySQL | 运维简单、行业常见 | 备选 |

---

## 二、云端表（8 张，Sprint-01 全部允许）

DDL 基于 PostgreSQL 语法。每张表须提供 downgrade。

### users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account         VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    plan_code       VARCHAR(50)  NOT NULL DEFAULT 'standard',
    status          VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_account ON users(account);
CREATE INDEX idx_users_status  ON users(status);
```

### devices
```sql
CREATE TABLE devices (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id),
    device_fingerprint_hash VARCHAR(255) NOT NULL,
    device_name             VARCHAR(255),
    status                  VARCHAR(20) NOT NULL DEFAULT 'active',
    first_seen_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_devices_user_id     ON devices(user_id);
CREATE INDEX idx_devices_fingerprint ON devices(device_fingerprint_hash);
CREATE INDEX idx_devices_status      ON devices(status);
```

### auth_sessions
```sql
CREATE TABLE auth_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    device_id           UUID NOT NULL REFERENCES devices(id),
    refresh_token_hash  VARCHAR(255) NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_auth_sessions_user_id    ON auth_sessions(user_id);
CREATE INDEX idx_auth_sessions_device_id  ON auth_sessions(device_id);
CREATE INDEX idx_auth_sessions_token_hash ON auth_sessions(refresh_token_hash);
```

### credit_accounts
```sql
CREATE TABLE credit_accounts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL UNIQUE REFERENCES users(id),
    plan_code     VARCHAR(50) NOT NULL,
    monthly_grant INTEGER NOT NULL DEFAULT 0,
    balance       INTEGER NOT NULL DEFAULT 0,
    period_start  TIMESTAMPTZ NOT NULL,
    period_end    TIMESTAMPTZ NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'active',
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### credit_ledger
```sql
CREATE TABLE credit_ledger (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id),
    change_type   VARCHAR(50) NOT NULL,
    amount        INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    source_type   VARCHAR(50),
    source_id     UUID,
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_credit_ledger_user_id    ON credit_ledger(user_id);
CREATE INDEX idx_credit_ledger_created_at ON credit_ledger(created_at);
```

### usage_events
```sql
CREATE TABLE usage_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    device_id   UUID NOT NULL REFERENCES devices(id),
    feature     VARCHAR(100) NOT NULL,
    event_type  VARCHAR(50)  NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_usage_events_user_id    ON usage_events(user_id);
CREATE INDEX idx_usage_events_feature    ON usage_events(feature);
CREATE INDEX idx_usage_events_created_at ON usage_events(created_at);
```

### provider_call_log
```sql
CREATE TABLE provider_call_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      VARCHAR(100) NOT NULL UNIQUE,
    user_id         UUID NOT NULL REFERENCES users(id),
    device_id       UUID NOT NULL REFERENCES devices(id),
    feature         VARCHAR(100) NOT NULL,
    provider        VARCHAR(50)  NOT NULL,
    model           VARCHAR(100) NOT NULL,
    input_units     INTEGER NOT NULL DEFAULT 0,
    output_units    INTEGER NOT NULL DEFAULT 0,
    image_units     INTEGER NOT NULL DEFAULT 0,
    gpu_seconds     DECIMAL(10,4) DEFAULT 0,
    raw_cost        DECIMAL(12,6) DEFAULT 0,
    estimated_cost  DECIMAL(12,6) DEFAULT 0,
    credits_charged INTEGER NOT NULL DEFAULT 0,
    currency        VARCHAR(10) NOT NULL DEFAULT 'CNY',
    status          VARCHAR(20) NOT NULL,
    error_code      VARCHAR(50),
    raw_usage       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_provider_log_user_id    ON provider_call_log(user_id);
CREATE INDEX idx_provider_log_request_id ON provider_call_log(request_id);
CREATE INDEX idx_provider_log_created_at ON provider_call_log(created_at);
```

### risk_logs
```sql
CREATE TABLE risk_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    device_id   UUID REFERENCES devices(id),
    ip_hash     VARCHAR(255),
    event_type  VARCHAR(100) NOT NULL,
    severity    VARCHAR(20)  NOT NULL DEFAULT 'low',
    details     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_risk_logs_created_at ON risk_logs(created_at);
```

---

## 三、本地 SQLite 表（4 张）

### ocr_history
```sql
CREATE TABLE ocr_history (
    id              TEXT PRIMARY KEY,
    image_path      TEXT NOT NULL,
    image_hash      TEXT,
    result_text     TEXT NOT NULL,
    result_blocks   TEXT,
    engine          TEXT NOT NULL DEFAULT 'paddleocr',
    provider        TEXT,
    duration_ms     INTEGER,
    estimated_cost  REAL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_ocr_history_created_at ON ocr_history(created_at);
```

### local_task_state
```sql
CREATE TABLE local_task_state (
    id            TEXT PRIMARY KEY,
    task_type     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    input_data    TEXT,
    output_data   TEXT,
    error_message TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### app_settings
```sql
CREATE TABLE app_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### offline_license_cache
```sql
CREATE TABLE offline_license_cache (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    device_id        TEXT NOT NULL,
    allowed_features TEXT,
    expires_at       TEXT NOT NULL,
    signature        TEXT NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 四、迁移执行顺序

1. 确认数据库选型 → 配置连接
2. 编写 Alembic 初始化迁移（含 downgrade）
3. 按外键依赖顺序建表：users → devices → auth_sessions → credit_accounts → credit_ledger → usage_events → provider_call_log → risk_logs
4. 开发环境验证
5. 桌面端 SQLite 在 Tauri 首次启动时建表

---

## 五、待确认事项

1. **数据库选型**：PostgreSQL 还是 MySQL？
2. **主键策略**：UUID v4 / UUID v7 / ULID / 自增整数？
3. **迁移工具**：Alembic 还是其他？
4. **本地 SQLite 迁移机制**：版本号文件 / 表内 schema_version？
5. **是否可以开始执行数据库迁移**？

---

> ⚠️ **此方案尚未执行。以上事项确认后方可启动迁移。**
