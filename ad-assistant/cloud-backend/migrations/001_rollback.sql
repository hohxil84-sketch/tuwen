-- S05-R03: RBAC — Rollback: remove role column from users table
-- Run: psql -d ad_assistant_dev -f migrations/001_rollback.sql

ALTER TABLE users DROP COLUMN IF EXISTS role;
