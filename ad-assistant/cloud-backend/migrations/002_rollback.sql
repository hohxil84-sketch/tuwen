-- S05-R06 rollback: remove idempotency_key and failed_at columns

DROP INDEX IF EXISTS uq_recharge_orders_user_idempotency;

ALTER TABLE recharge_orders
    DROP COLUMN IF EXISTS idempotency_key;

ALTER TABLE recharge_orders
    DROP COLUMN IF EXISTS failed_at;
