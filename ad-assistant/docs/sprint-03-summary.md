# Sprint-03 Summary

Date: 2026-06-02
Base branch: `main`
Current verified head: `3bbfafb` (S03-T04 merged; sprint closed)

**Sprint-03 is closed.** All four sprint tasks + one standards enhancement + one CI hotfix have been merged to `main`.

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| Standards | Coding Standards Extensibility Guidelines | PR #30 / `fe4da23` |
| S03-T01 | Security & Reliability Fixes (4× P0) | PR #28 / `0c1096b` |
| S03-T02 | DeepSeek Chat API as first real AI Provider | PR #32 / `1773ab4` |
| S03-T03 | Real credit deduction after AI Provider calls | PR #33 / `8fcf6f5` |
| S03-T04 | Desktop Dashboard UI Redesign | PR #34 / `3bbfafb` |
| Hotfix | CI pg-integration missing `openai` dependency | PR #35 / `abd8646` |

## Current Capability

- **Security baseline hardened**: auto device fingerprint (crypto.randomUUID), unified token store, 30s fetch timeout (AbortController), `_log_risk` exception logging.
- **First real AI Provider live**: DeepSeek Chat API (`deepseek-chat`) — `mock_ad_copy` + `standard` plan routes to DeepSeek; real API key → real ad copy.
- **Credit deduction wired**: each successful Provider call deducts credits from user balance via atomic `deduct_credits()`, writes `credit_ledger`, and returns `credits_charged` to the client.
- **Desktop Dashboard UI**: dark SaaS workbench shell with sidebar nav (4 groups), topbar, stat cards, quick entries (OCR clickable), recent orders mock table, recent images mock grid. 1366px canvas with proportional scale.
- **CI**: pg-integration workflow includes `openai` dependency; all PRs pass CI.

## Safety Boundaries

- DeepSeek API key read from Settings only — never hardcoded or exposed to clients.
- Credit deduction is atomic (single transaction: balance decrement + ledger insert).
- Pre-deduction balance check is NOT implemented — a user with 0 balance can still call and succeed (credits_charged=0).
- Desktop mock data is frontend-only; no real API integration in dashboard yet.
- Dashboard quick entries (except OCR) are disabled + "即将开放".

## Verification Summary

| Task | Tests | Result |
|------|-------|--------|
| S03-T01 | Backend regression 167 passed, Desktop build 43 modules 0 errors, CI pg-integration | ✅ |
| S03-T02 | DeepSeek focused 25 passed, Full regression 192 passed 55 skipped, CI | ✅ |
| S03-T03 | Credit focused 19 passed, Full regression 211 passed 55 skipped, CI | ✅ |
| S03-T04 | Desktop build 62 modules 0 errors, `git diff --check`, CI pg-integration | ✅ |

## Residual Risks

1. **余额不足无拦截**: 用户余额为 0 时 Provider 调用仍成功但不扣费，需预扣检查（pre-flight balance check）。
2. **DeepSeek 无降级**: DeepSeek 不可用时无 fallback/retry，调用直接失败。
3. **Tauri 系统 chrome**: 桌面窗口顶部白色标题栏来自 Windows 原生 chrome，深色主题需独立 Tauri 任务。
4. **Dashboard 纯 mock**: 仪表盘数据为前端 mock，未接入真实后端统计/订单/图片数据。
5. **快捷入口未全接**: OCR 外 5 个快捷入口均为 disabled 占位。
6. **CI Node.js 20 弃用警告**: GitHub Actions 将于 2026-09-16 移除 Node.js 20 runner。

## Next-Stage (Sprint-04 Candidates)

These are candidates only. Create a new task document and new branch before implementation.

- Provider fallback / retry / health-check mechanisms.
- Pre-flight balance check (余额不足拦截).
- Local OCR history retention, cleanup, and privacy policy.
- Tauri 深色标题栏 + EXE packaging.
- Dashboard data integration (real API replacing mock data).
- Membership / package / recharge / grant-balance flows.
- 快捷入口逐个接入真实功能（图文生成、视频生成等）。
