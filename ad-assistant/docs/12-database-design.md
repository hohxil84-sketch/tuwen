# 12 数据库设计

## 状态

本文档是数据库设计草案。

真正创建或修改数据库表结构属于重大变更，必须先确认。

> Sprint-02 Task-07 已对齐 ORM `DateTime(timezone=True)` 与 DDL `TIMESTAMPTZ`。
> 所有云端表的时间列统一使用 PostgreSQL `TIMESTAMPTZ`（存储 UTC），
> SQLAlchemy 模型对应使用 `DateTime(timezone=True)`。

## MVP 表

Sprint-01 允许设计以下基础表：
- users
- devices
- auth_sessions
- credit_accounts
- credit_ledger
- usage_events
- provider_call_log
- risk_logs

## users

用途：用户基础信息。

字段草案：
- id
- account
- password_hash
- plan_code
- status
- created_at
- updated_at

禁止保存明文密码。

## devices

用途：设备绑定。

字段草案：
- id
- user_id
- device_fingerprint_hash
- device_name
- status
- first_seen_at
- last_seen_at
- created_at
- updated_at

## auth_sessions

用途：Token 刷新和会话管理。

字段草案：
- id
- user_id
- device_id
- refresh_token_hash
- expires_at
- revoked_at
- created_at
- updated_at

禁止保存明文 refresh token。

## credit_accounts

用途：用户 AI 算力余额。

字段草案：
- id
- user_id
- plan_code
- monthly_grant
- balance
- period_start
- period_end
- status
- updated_at

## credit_ledger

用途：算力流水。

字段草案：
- id
- user_id
- change_type
- amount
- balance_after
- source_type
- source_id
- description
- created_at

扣费必须写流水。

## usage_events

用途：使用统计。

字段草案：
- id
- user_id
- device_id
- feature
- event_type
- metadata
- created_at

客户端可提交使用事件，但不得提交最终扣费结果。

## provider_call_log

用途：记录所有 Provider 调用和成本。

字段草案：
- id
- request_id
- user_id
- device_id
- feature
- provider
- model
- input_units
- output_units
- image_units
- gpu_seconds
- raw_cost
- estimated_cost
- credits_charged
- currency
- status
- error_code
- raw_usage
- created_at

所有云端 AI 调用必须写入本表。

## risk_logs

用途：风控审计。

字段草案：
- id
- user_id
- device_id
- ip_hash
- event_type
- severity
- details
- created_at

## 本地 SQLite 表

桌面端本地允许：
- ocr_history
- local_task_state
- app_settings
- offline_license_cache

不得明文保存 Token、密码、Provider Key。

