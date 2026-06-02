-- S05-R03: RBAC — Add role column to users table
-- Run: psql -d ad_assistant_dev -f migrations/001_add_user_role.sql

ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

-- Bootstrap: promote the first admin (replace with actual user UUID)
-- UPDATE users SET role = 'admin' WHERE id = '<admin-user-uuid>';
