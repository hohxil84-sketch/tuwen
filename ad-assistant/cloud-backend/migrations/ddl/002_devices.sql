-- 002_devices.sql
-- Sprint-01 Auth/Device — devices table (PostgreSQL)

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

-- Downgrade:
-- DROP TABLE IF EXISTS devices CASCADE;
