# Sprint-04 Summary

Date: 2026-06-02
Base branch: `main`
Current verified head: `a31cf0a` (S04-T10 merged; sprint closed)

**Sprint-04 is closed.** All ten sprint tasks + four rules/workflow enhancements have been merged to `main`.

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| S04-T01 | Provider Reliability — pre-flight balance check + fallback/retry | PR #37 / `b476e0c` |
| S04-T02 | Dashboard data integration + AI ad copy entry | PR #38 / `497319d` |
| S04-T03 | Local OCR history cleanup & privacy | PR #39 / `223482b` |
| S04-T04 | Membership / package / recharge / admin grant | PR #40 / `11b2737` |
| S04-T05 | Desktop shortcut entries → real features | PR #44 / `af594ed` |
| S04-T06 | Tauri dark titlebar audit (BLOCKED → docs) | `b6e8e9f` |
| S04-T07 | Tauri source init + frameless dark titlebar | PR #46 / `0d2684e` |
| S04-T08 | Tauri EXE package & smoke verification | PR #48 / `dba4888` |
| S04-T09 | Tauri beta brand icon replacement | PR #50 / `3bd6238` |
| S04-T10 | Tauri frameless window boundary & depth (CSS) | PR #51 / `a31cf0a` |
| Rules | Reviewer-mode guardrail after self-review | PR #41 / `7c4a6f3` |
| Rules | Codex task spec writing & CC execution rules | PR #43 / `2432d13` |
| Rules | CC task-document modification limits | PR #45 / `9e1f1aa` |
| Rules | Local install location D: drive rule | PR #49 / `6efe32a` |

## Current Capability

### Cloud AI / Credit

- **Provider reliability**: 2-level balance gate — absolute min (1 credit) + feature min (`FEATURE_MIN_CREDITS` dict). `InsufficientBalanceError` → writes `provider_call_log` + API returns 402 with Chinese prompt. Provider degradation chain `deepseek → mock` (1 level). Transient fault retry: max 2 retries with exponential backoff 1s→2s for TIMEOUT/CONNECTION_ERROR/API_ERROR.
- **Real AI ad copy**: `POST /api/v1/mock-ai/ad-copy` → DeepSeek Chat API (`deepseek-chat`) for `mock_ad_copy` + `standard` plan. Real API key → real ad copy.
- **Credit deduction**: Atomic `deduct_credits()` (balance decrement + ledger insert in single transaction), `cny_to_credits()` conversion (¥1 = 100 credits, ceil rounding). `credits_charged` propagated to API response.

### Membership / Billing

- **Plans**: 3 tiers (basic/standard/pro) with name, credits, price. `GET /api/v1/plans` (public, no auth).
- **Recharge**: `POST /api/v1/credits/recharge` (logged-in). Simulated payment → instant credit grant via `grant_credits()`. Writes `recharge_orders` + `credit_ledger`.
- **Admin grant**: `POST /api/v1/admin/credits/grant` (hardcoded admin whitelist in config). No RBAC.
- **Desktop UI**: `MembershipPage.vue` — current plan banner, 3-column plan comparison, recharge confirmation modal, order history table. Sidebar "会员中心" nav + `/membership` route.

### Desktop Dashboard

- **Data integration**: `GET /api/v1/dashboard/summary` returns aggregated stats + recent orders. Dashboard stat cards and recent orders table powered by real API, with mock fallback + loading skeletons.
- **Quick entries**: OCR (`/ocr`) + AI ad copy (`/ai-ad-copy`) enabled and wired to real pages. Remaining 4 entries disabled with "即将开放" visual treatment.
- **Sidebar**: "AI 文案生成" enabled (route `/ai-ad-copy`) since S04-T05. OCR, 会员中心, 使用日志 all confirmed navigable.

### OCR & Local History

- **Delete/Clear**: `DELETE /local/ocr/history/{record_id}` + `DELETE /local/ocr/history` (clear all). Sandbox image file cleanup on delete; orphaned files tolerated (non-blocking).
- **UI**: HistoryPage toolbar with delete buttons, inline confirmation for single delete, modal confirmation for clear-all.

### Tauri Desktop

- **Engine**: Tauri 2.11.2 source initialized — 10 config files (Cargo.toml, main.rs, lib.rs, tauri.conf.json, capabilities, build.rs, .gitignore, icons). `package.json` with `@tauri-apps/api` + `@tauri-apps/cli`.
- **Frameless window**: `decorations: false` + custom AppTopbar titlebar with `data-tauri-drag-region` + min/max/close buttons via `@tauri-apps/api/window`. Window control buttons auto-hidden in browser dev mode.
- **Build**: `npm run tauri build` produces MSI (2.7 MB) + NSIS installer; bare EXE (8.2 MB). Product name "AdAssistant" (ASCII for WiX v3 compat).
- **Brand**: Beta icon — dark rounded background + geometric "A" + cyan→blue gradient. `icon.ico` (7 sizes 16–256 px) + `icon.png` (128×128 RGBA).
- **Appearance**: CSS inner border `1px solid rgba(148,163,184,0.10)` + inner shadow `inset 0 0 40px rgba(0,0,0,0.30)` for frameless window depth perception.
- **Capabilities**: Minimal — `core:window` only (7 permissions: minimize, toggle-maximize, close, is-maximized, set-fullscreen, start-dragging, default). No shell, fs, path, http, clipboard, notification, updater.

## Safety Boundaries

- Pre-flight balance check prevents Provider calls when balance < feature min. `InsufficientBalanceError` does NOT trigger provider degradation — user must recharge.
- Provider degradation is static 1-level (deepseek → mock). No circuit breaker, health check, or multi-level chain.
- Credit deduction is atomic (single transaction: balance decrement + ledger insert). Deduction failure is recorded and re-raised.
- Admin credit grant uses hardcoded `ADMIN_USER_IDS` list in config. No roles, permissions, or authentication-based admin guard.
- Simulated payment (recharge) has no fraud controls, rate limiting, or amount caps.
- Monthly credit auto-grant scheduler is NOT implemented — packages describe credits but there is no automated periodic grant.
- DeepSeek API key read from Settings only — never hardcoded, logged, or exposed to clients.
- Tauri capabilities locked to `core:window` only. No filesystem, shell, or network permissions beyond the Vite dev proxy.
- Desktop auth tokens are memory-only (Pinia store). Not persisted to localStorage, files, SQLite, cookies, or Tauri storage.
- Build artifacts (EXE/MSI/NSIS installer, `src-tauri/target/`) are NOT committed.
- Frameless window has NO native Windows DWM shadow. Current CSS solution is a visual workaround, not a substitute for native window chrome.

## Verification Summary

| Task | Tests | Result |
|------|-------|--------|
| S04-T01 | Focused 29 passed, Full regression 241 passed + 55 skipped | ✅ |
| S04-T02 | Focused 9 passed, Full regression 250 passed + 55 skipped | ✅ |
| S04-T03 | Unit (history) 19 passed + API 23 passed = 42 total | ✅ |
| S04-T04 | Focused 29 passed, Full regression 279 passed + 57 skipped | ✅ |
| S04-T05 | `npm run build` 68 modules 0 errors, `git diff --check` | ✅ |
| S04-T06 | Audit only — no code changes to test | ✅ |
| S04-T07 | `npm run build` 74 modules 0 errors, `cargo build` 355 crates, `tauri dev` OK | ✅ |
| S04-T08 | `npm run build` 74 modules, `npm run tauri build` MSI + NSIS generated | ✅ |
| S04-T09 | `npm run build` 74 modules, `npm run tauri build` EXE + MSI generated | ✅ |
| S04-T10 | `npm run build` 74 modules 0 errors, `git diff --check` | ✅ |

Backend regression test count grew from 167 (S03 closeout) to 279 passed (S04 closeout), reflecting new test suites for provider reliability, dashboard, credit deduction, membership, and recharge.

## Residual Risks

1. **未签名安装包**: EXE/MSI/NSIS 无 Authenticode 代码签名证书，Windows SmartScreen 弹出"Windows protected your PC"警告，需用户手动点击"More info" → "Run anyway"。
2. **NSIS 下载网络不稳定**: `npm run tauri build` 中 NSIS 二进制从 GitHub Releases 下载，国内网络偶发超时，需重试或预缓存 NSIS zip。
3. **正式品牌 VI 未确认**: 当前图标为临时内测几何 "A" 标识。正式品牌 logo、字体、配色、VI 体系尚未设计，桌面图标和网站 favicon 仍需替换。
4. **CSS 窗口阴影 ≠ 原生 DWM 阴影**: Frameless 窗口缺少 Windows DWM 外部投射阴影。当前 `box-shadow: inset` 方案仅在窗口内部产生暗角，在浅色桌面背景下层次感有限。正式方案需接入 DWM API 或 Tauri window-shadows 插件（高风险，需独立任务）。
5. **模拟支付无风控**: Recharge 为 simulated 即时到账，无支付渠道集成、回调验签、限额、风控或异常检测。
6. **管理员白名单无 RBAC**: Admin grant 端点仅靠 `settings.ADMIN_USER_IDS` 白名单（硬编码 user_id 列表），无角色、权限层级或审计日志。
7. **后台管理能力不足**: 无管理后台 UI。缺少用户管理、订单查询、数据报表、Provider 监控、系统配置、积分调整等管理功能。
8. **Tauri 权限过于最小化**: 当前仅 `core:window` 7 项。未来如需文件读写、桌面通知、自动更新、本地服务进程管理，需逐步开放 capabilities 并审计安全影响。
9. **人工 GUI/E2E 验证缺口**: S04-T07 至 S04-T10 仅通过前端构建和 Tauri 编译验证，缺少在真实 Windows 桌面执行的全功能人工验证（安装→启动→登录→各页面→窗口操作→卸载）。
10. **月度积分发放调度器未实现**: 套餐月度赠送积分需 cron/后台任务调度，当前套餐购买后积分一次性到账，后续月份不自动发放。
11. **Provider 无熔断器/健康检查**: 降级为静态 1 级链，无运行时健康状态监测、熔断、半开恢复或自适应降级。
12. **余额不足 402 用户体验**: 桌面端收到 402 后仅有错误提示，无引导跳转充值页面的流程。

## Next-Stage (Sprint-05 Candidates)

这些是候选方向，不是已启动任务。每个方向启动前必须创建独立任务单、分支和 PR。

### 内测分发准备（建议优先）

- 代码签名证书申请与 Tauri bundle 签名集成
- NSIS 安装包离线打包与稳定性
- Windows SmartScreen 信誉建立方案
- Tauri updater 自动更新基础设施
- 内测用户邀请码/激活码机制
- 安装指引与已知问题文档

### 基础后台 / 管理端

- 管理后台最小 UI（用户列表、订单查询、积分授予、Provider 调用日志）
- RBAC 角色权限体系（替换硬编码 `ADMIN_USER_IDS`）
- Provider 监控面板（调用量、成功率、延迟、成本趋势）
- 系统配置管理界面
- 管理员操作审计日志

### 商业链路加固

- 真实支付渠道集成（微信支付/支付宝）
- 支付回调验签 + 订单状态机（pending → paid → expired/cancelled）
- 风控基础（充值限额、频率限制、异常检测）
- 月度积分自动发放调度器（cron/background task）
- 退款逻辑与积分扣回

### 端到端 Smoke / 回归验证

- 桌面端全功能人工 E2E 验证 runbook（登录→OCR→AI 文案→会员→充值→历史清理→窗口控制→安装/卸载）
- 后端 API 性能基线测试
- 多 Windows 版本兼容性验证（Windows 10 22H2 / Windows 11 23H2）
- 不同 DPI/缩放设置的 UI 验证

### P1 功能探索（必须用户确认后才能启动）

以下功能当前为 `MVP_OPTIONAL`，不得在用户明确确认前启动：

- 转矢量（P1）
- 基础修图（P1）
- 高级 AI 修图（P1）
- AI 门头效果图（P1）

BACKLOG 和 FUTURE 功能（PPT、Skill 市场、插件系统、AI 工作流、自动报价、微信机器人、云同步、PS/CDR 自动控制、企业私有部署等）状态不变，当前禁止开发。

## Sprint-04 Closeout

All planned Sprint-04 tasks are merged. No tasks remain in progress.

Key deliverables across the sprint:

- **Provider reliability hardened**: balance gate + degradation chain + transient retry — the AI call path is now guarded against both underfunded users and transient Provider failures.
- **Dashboard data integration**: first real backend aggregation API powering desktop dashboard stats and orders — desktop is no longer pure mock.
- **OCR privacy**: users can delete individual history records or clear all, with sandbox file cleanup.
- **Full membership/recharge billing flow**: 3-tier plans, simulated recharge, admin credit grant — the billing skeleton is in place for real payment integration.
- **Desktop shortcut wiring**: sidebar and dashboard entries now connect to real OCR, AI ad copy, membership, and history pages.
- **Tauri desktop app**: the project is now a real, buildable, installable Tauri 2 Windows application — engine init → frameless dark titlebar → EXE/MSI/NSIS packaging → brand icon → window depth polish.
- **4 rules/workflow enhancements**: reviewer-mode guardrail, Codex task spec rules, CC modification limits, and local install location rules solidified CC autonomy within safe boundaries.

The desktop app produces unsigned but functional Windows installers. The next natural priority tier is **内测分发准备** (code signing, updater, invite codes) followed by **基础后台/管理端** and **商业链路加固**.
