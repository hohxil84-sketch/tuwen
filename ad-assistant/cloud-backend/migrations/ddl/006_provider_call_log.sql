-- 006_provider_call_log.sql
-- Sprint-01 Usage/Provider Log — provider_call_log table (PostgreSQL)

CREATE TABLE provider_call_log (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id        VARCHAR(255),
    user_id           UUID REFERENCES users(id),
    device_id         UUID REFERENCES devices(id),
    provider          VARCHAR(100) NOT NULL,
    model             VARCHAR(100) NOT NULL,
    feature           VARCHAR(100) NOT NULL,
    status            VARCHAR(20)  NOT NULL,
    error_code        VARCHAR(100),
    prompt_tokens     INTEGER      NOT NULL DEFAULT 0,
    completion_tokens INTEGER      NOT NULL DEFAULT 0,
    total_tokens      INTEGER      NOT NULL DEFAULT 0,
    estimated_cost    NUMERIC(12,8),
    credits_charged   INTEGER      DEFAULT 0,
    latency_ms        INTEGER,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- CHECK 约束
    CONSTRAINT chk_provider_call_log_status
        CHECK (status IN ('success', 'error')),
    CONSTRAINT chk_provider_call_log_error_code
        CHECK ((status = 'error' AND error_code IS NOT NULL)
            OR (status = 'success' AND error_code IS NULL)),
    CONSTRAINT chk_provider_call_log_prompt_tokens
        CHECK (prompt_tokens >= 0),
    CONSTRAINT chk_provider_call_log_completion_tokens
        CHECK (completion_tokens >= 0),
    CONSTRAINT chk_provider_call_log_total_tokens
        CHECK (total_tokens >= 0),
    CONSTRAINT chk_provider_call_log_estimated_cost
        CHECK (estimated_cost IS NULL OR estimated_cost >= 0),
    CONSTRAINT chk_provider_call_log_credits_charged
        CHECK (credits_charged IS NULL OR credits_charged >= 0),
    CONSTRAINT chk_provider_call_log_latency_ms
        CHECK (latency_ms IS NULL OR latency_ms >= 0)
);

CREATE INDEX idx_provider_call_log_user_id    ON provider_call_log(user_id);
CREATE INDEX idx_provider_call_log_device_id  ON provider_call_log(device_id);
CREATE INDEX idx_provider_call_log_provider   ON provider_call_log(provider);
CREATE INDEX idx_provider_call_log_feature    ON provider_call_log(feature);
CREATE INDEX idx_provider_call_log_status     ON provider_call_log(status);
CREATE INDEX idx_provider_call_log_created_at ON provider_call_log(created_at);

-- Downgrade:
-- DROP TABLE IF EXISTS provider_call_log CASCADE;
