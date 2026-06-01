-- 010_recharge_orders.sql
-- Sprint-04 Task-04 — recharge_orders table (PostgreSQL)
-- 用户充值/购买套餐订单记录。当前使用 simulated 支付方式。

CREATE TABLE recharge_orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id),
    plan_code       VARCHAR(50),                       -- 购买的套餐 code，可为空（自定义金额充值）
    amount_cny      INTEGER      NOT NULL,             -- 充值金额，单位：元
    credits         INTEGER      NOT NULL,             -- 获得的 AI 算力积分
    payment_method  VARCHAR(50)  NOT NULL DEFAULT 'simulated',
    status          VARCHAR(20)  NOT NULL DEFAULT 'completed',
    description     TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_recharge_orders_amount_cny CHECK (amount_cny > 0),
    CONSTRAINT chk_recharge_orders_credits CHECK (credits > 0),
    CONSTRAINT chk_recharge_orders_payment_method
        CHECK (payment_method IN ('simulated', 'alipay', 'wechat_pay', 'stripe', 'manual', 'offline')),
    CONSTRAINT chk_recharge_orders_status
        CHECK (status IN ('pending', 'completed', 'cancelled', 'refunded'))
);

CREATE INDEX idx_recharge_orders_user_id    ON recharge_orders(user_id);
CREATE INDEX idx_recharge_orders_created_at ON recharge_orders(created_at DESC);
CREATE INDEX idx_recharge_orders_status     ON recharge_orders(status);

-- Downgrade:
-- DROP TABLE IF EXISTS recharge_orders CASCADE;
