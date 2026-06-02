-- S05-R06: 模拟充值风控与订单状态加固
-- Add idempotency_key and failed_at columns to recharge_orders

ALTER TABLE recharge_orders
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64);

ALTER TABLE recharge_orders
    ADD COLUMN IF NOT EXISTS failed_at TIMESTAMPTZ;

-- Partial unique index to enforce one active idempotency_key per user.
-- NULL idempotency_key values are NOT constrained (they represent requests
-- without idempotency protection, which is the legacy / backward-compat path).
-- Only non-null keys must be unique per user, and only for non-failed orders
-- (failed orders can be retried with a new idempotency_key).
CREATE UNIQUE INDEX IF NOT EXISTS uq_recharge_orders_user_idempotency
    ON recharge_orders (user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL AND status <> 'failed';
