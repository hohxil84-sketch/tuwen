-- 007_credit_accounts.sql
-- Sprint-02 Task-02 — credit_accounts table (PostgreSQL)
-- 用户 AI 算力余额账户，每个用户最多一个 active 记录。

CREATE TABLE credit_accounts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users(id),
    plan_code     VARCHAR(50) NOT NULL DEFAULT 'standard',
    monthly_grant INTEGER     NOT NULL DEFAULT 0,
    balance       INTEGER     NOT NULL DEFAULT 0,
    period_start  TIMESTAMPTZ,
    period_end    TIMESTAMPTZ,
    status        VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 每个用户最多一个 active 账户基础记录
    CONSTRAINT uq_credit_accounts_user_id UNIQUE (user_id),

    CONSTRAINT chk_credit_accounts_monthly_grant
        CHECK (monthly_grant >= 0),

    CONSTRAINT chk_credit_accounts_balance
        CHECK (balance >= 0),

    CONSTRAINT chk_credit_accounts_status
        CHECK (status IN ('active', 'disabled')),

    CONSTRAINT chk_credit_accounts_period
        CHECK (period_start IS NULL OR period_end IS NULL OR period_end > period_start)
);

CREATE INDEX idx_credit_accounts_user_id ON credit_accounts(user_id);
CREATE INDEX idx_credit_accounts_status   ON credit_accounts(status);

-- Downgrade:
-- DROP TABLE IF EXISTS credit_accounts CASCADE;
