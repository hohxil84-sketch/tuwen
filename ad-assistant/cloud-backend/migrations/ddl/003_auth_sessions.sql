-- 003_auth_sessions.sql
-- Sprint-01 Auth/Device — auth_sessions table (PostgreSQL)

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

-- Downgrade:
-- DROP TABLE IF EXISTS auth_sessions CASCADE;
