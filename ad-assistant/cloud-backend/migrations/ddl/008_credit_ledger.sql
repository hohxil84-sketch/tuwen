-- 008_credit_ledger.sql
-- Sprint-02 Task-02 — credit_ledger table (PostgreSQL)
-- 用户 AI 算力流水，记录余额变动的完整审计轨迹。

CREATE TABLE credit_ledger (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID         NOT NULL REFERENCES users(id),
    account_id    UUID         REFERENCES credit_accounts(id),
    change_type   VARCHAR(30)  NOT NULL,
    amount        INTEGER      NOT NULL,
    balance_after INTEGER      NOT NULL,
    source_type   VARCHAR(50)  NOT NULL,
    source_id     VARCHAR(255),
    description   VARCHAR(255),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_credit_ledger_change_type
        CHECK (change_type IN ('grant', 'consume', 'refund', 'adjust')),

    CONSTRAINT chk_credit_ledger_amount_nonzero
        CHECK (amount <> 0),

    CONSTRAINT chk_credit_ledger_balance_after
        CHECK (balance_after >= 0),

    CONSTRAINT chk_credit_ledger_source_type
        CHECK (source_type IN ('system', 'provider_call', 'manual', 'order')),

    -- consume 类型必须 amount < 0
    CONSTRAINT chk_credit_ledger_consume_negative
        CHECK (change_type <> 'consume' OR amount < 0)
);

CREATE INDEX idx_credit_ledger_user_id     ON credit_ledger(user_id);
CREATE INDEX idx_credit_ledger_account_id  ON credit_ledger(account_id);
CREATE INDEX idx_credit_ledger_created_at  ON credit_ledger(created_at);
CREATE INDEX idx_credit_ledger_change_type ON credit_ledger(change_type);

-- Downgrade:
-- DROP TABLE IF EXISTS credit_ledger CASCADE;
