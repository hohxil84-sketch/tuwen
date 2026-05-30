-- 005_usage_events.sql
-- Sprint-01 Usage/Provider Log — usage_events table (PostgreSQL)

CREATE TABLE usage_events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id),
    device_id     UUID REFERENCES devices(id),
    event_type    VARCHAR(100) NOT NULL,
    feature       VARCHAR(100) NOT NULL,
    request_id    VARCHAR(255),
    metadata_json JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_events_user_id    ON usage_events(user_id);
CREATE INDEX idx_usage_events_device_id  ON usage_events(device_id);
CREATE INDEX idx_usage_events_feature    ON usage_events(feature);
CREATE INDEX idx_usage_events_created_at ON usage_events(created_at);

-- Downgrade:
-- DROP TABLE IF EXISTS usage_events CASCADE;
