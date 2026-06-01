-- 009_plans.sql
-- Sprint-04 Task-04 — plans table (PostgreSQL)
-- 会员套餐/方案定义表，存储可用套餐的元数据和定价。

CREATE TABLE plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,              -- e.g. "标准版"
    code            VARCHAR(50)  NOT NULL UNIQUE,        -- e.g. "standard"
    price_cny       INTEGER      NOT NULL,              -- 月费，单位：元
    monthly_credits INTEGER      NOT NULL DEFAULT 0,    -- 每月赠送 AI 算力额度
    features_json   TEXT,                               -- JSON array of feature strings
    sort_order      INTEGER      NOT NULL DEFAULT 0,
    status          VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_plans_price_cny CHECK (price_cny >= 0),
    CONSTRAINT chk_plans_monthly_credits CHECK (monthly_credits >= 0),
    CONSTRAINT chk_plans_status CHECK (status IN ('active', 'inactive'))
);

CREATE INDEX idx_plans_code   ON plans(code);
CREATE INDEX idx_plans_status ON plans(status);

-- Seed data: 3 membership tiers
INSERT INTO plans (name, code, price_cny, monthly_credits, features_json, sort_order) VALUES
(
    '标准版', 'standard', 359, 500,
    '["AI 文案生成", "OCR 文字识别", "基础图片处理", "每月 500 算力额度"]',
    1
),
(
    '专家版', 'expert', 559, 1000,
    '["AI 文案生成", "AI 效果图生成", "OCR 文字识别", "图片改尺寸", "智能抠图", "每月 1000 算力额度", "优先客服支持"]',
    2
),
(
    '企业版', 'enterprise', 999, 2000,
    '["AI 文案生成", "AI 效果图生成", "OCR 文字识别", "批量处理", "拼版助手", "图片改尺寸", "每月 2000 算力额度", "专属客户经理", "API 接口对接"]',
    3
);

-- Downgrade:
-- DROP TABLE IF EXISTS plans CASCADE;
