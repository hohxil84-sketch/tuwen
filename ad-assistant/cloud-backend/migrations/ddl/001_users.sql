-- 001_users.sql
-- Sprint-01 Auth/Device — users table (PostgreSQL)

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

-- Downgrade:
-- DROP TABLE IF EXISTS users CASCADE;
