-- 004_risk_logs.sql
-- Sprint-01 Auth/Device — risk_logs table (PostgreSQL)

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
CREATE INDEX idx_risk_logs_event_type ON risk_logs(event_type);

-- Downgrade:
-- DROP TABLE IF EXISTS risk_logs CASCADE;
