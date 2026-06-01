# Current Task: Sprint-03 Task-01 Security & Reliability Fixes

## Status

`IN_PROGRESS`

## Background

Sprint-02 全面审查发现了 4 个 P0 安全和可靠性问题，必须在 Sprint-03 新功能开发前修复。

## Goal

修复 4 个 P0 审查发现，提升安全性和可靠性基线。

## What To Build

### D1: Auto-generate device fingerprint (Desktop)

- **当前问题**: `LoginPage.vue` 中 device_fingerprint 为手动文本输入，用户可输入任意值，完全绕过设备绑定安全机制
- **修复方案**:
  1. 首次启动时生成随机 UUID 作为 device_fingerprint
  2. 持久化到 localStorage（fingerprint 非密钥，可持久化）
  3. 登录表单自动读取，移除手动输入框
  4. 提供「重置设备指纹」按钮（仅开发/调试用）

### D2: Unify token to Pinia store (Desktop)

- **当前问题**: access token 在 `cloudApi.ts`(module-level var) 和 `authStore.ts`(Pinia ref) 双源存储，可能漂移
- **修复方案**:
  1. `cloudApi.ts` 从 `authStore.ts` 读取 token，移除独立 `accessToken` 变量
  2. `cloudApi.ts` 提供 `getAccessToken`/`setAccessToken` 作为 store 的 thin wrapper
  3. 确保只有 store 的 action 能修改 token

### D3: Add request timeouts (Desktop)

- **当前问题**: 所有 `fetch()` 无超时，服务端挂起会导致 UI 永久卡住
- **修复方案**:
  1. 为 `cloudApi.ts` 和 `ocrService.ts` 的所有 fetch 添加 `AbortController`
  2. 默认超时 30s
  3. 超时时抛出 `AbortError`，UI 层显示友好提示

### D4: Add logging to _log_risk (Backend)

- **当前问题**: `auth_service.py:_log_risk` 中 `except Exception: pass` 静默吞没所有异常
- **修复方案**:
  1. 添加 `logging.exception()` 记录异常
  2. 保持不中断主流程的行为

## What Not To Build

- 不改变设备绑定后端逻辑
- 不改变 token 刷新机制
- 不新增桌面端页面或功能
- 不修改 DDL、API contract、provider、credit
- 不新增依赖

## Allowed Files

### Desktop
- `desktop-app/src/stores/authStore.ts`
- `desktop-app/src/services/cloudApi.ts`
- `desktop-app/src/services/ocrService.ts`
- `desktop-app/src/pages/LoginPage.vue`

### Backend
- `cloud-backend/app/services/auth_service.py`

### Docs
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- 所有其他文件（与 S03-T01 无关）

## Acceptance Criteria

1. Device fingerprint 自动生成并持久化，用户无需手动输入
2. Token 只有 Pinia store 一个源头
3. 所有 fetch 调用有超时保护
4. `_log_risk` 异常被记录到日志
5. Backend tests 全部通过（167+）
6. Desktop `npm run build` 通过
7. `git diff --check` 通过

## Major Change Status

**Yes** — 涉及 Auth/Device 安全机制（D1 设备指纹生成方式变更）。用户已确认。

## Suggested Branch

`feature/sprint-03-task-01-security-fixes`
