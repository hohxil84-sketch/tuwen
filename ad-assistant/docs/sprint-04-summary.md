# Sprint-04 Summary（残余风险跟踪版）

Date: 2026-06-02
E2E Smoke 分支: `risk/sprint-04-e2e-smoke`
Current main HEAD: `a31cf0a`

> 注：本文档是 Sprint-04 残余风险的 E2E 压实跟踪版本。完整的 Sprint-04 closeout summary 参见 `docs/sprint-04-summary.md` 的独立 closeout 版本（PR #52 已回滚，可按需重建）。

## Sprint-04 已完成模块（摘要）

| Task | Scope | PR |
|------|-------|-----|
| S04-T01 | Provider Reliability — pre-flight balance check + fallback/retry | #37 |
| S04-T02 | Dashboard data integration + AI ad copy entry | #38 |
| S04-T03 | Local OCR history cleanup & privacy | #39 |
| S04-T04 | Membership / package / recharge / admin grant | #40 |
| S04-T05 | Desktop shortcut entries → real features | #44 |
| S04-T06 | Tauri dark titlebar audit (BLOCKED → docs) | — |
| S04-T07 | Tauri source init + frameless dark titlebar | #46 |
| S04-T08 | Tauri EXE package & smoke verification | #48 |
| S04-T09 | Tauri beta brand icon replacement | #50 |
| S04-T10 | Tauri frameless window boundary & depth (CSS) | #51 |

## E2E Smoke 验证结果

详见 [28-sprint-04-e2e-smoke.md](28-sprint-04-e2e-smoke.md)。

| 验证类别 | PASS | BLOCKED_BY_ENV | NOT_RUN |
|---------|------|----------------|---------|
| 自动化验证 (6) | 5 | 1 | 0 |
| 代码静态验证 (7) | 7 | 0 | 0 |
| 打包产物 (5) | 3 | 0 | 2 |
| GUI 链路 (8) | 0 | 0 | 8（需 GUI 环境） |

## 残余风险 E2E 压实状态

| # | 残余风险 | 严重度 | E2E 后状态 | 后续 |
|---|---------|--------|-----------|------|
| 1 | 未签名安装包 — SmartScreen 警告 | 高 | 仍待修复 | Sprint-05: 代码签名证书 |
| 2 | NSIS 下载网络不稳定 | 中 | **已缓解** — 本次下载成功 | 建议预缓存 NSIS zip |
| 3 | 正式品牌 VI 未确认 | 低 | 仍待确认 | 等用户决策 |
| 4 | CSS 窗影 ≠ 原生 DWM 阴影 | 中 | 仍待专项 | Sprint-05 可选: DWM API 接入 |
| 5 | 模拟支付无风控 | 高 | 仍待修复 | Sprint-05: 支付风控 |
| 6 | 管理员白名单无 RBAC | 高 | 仍待修复 | Sprint-05: RBAC 体系 |
| 7 | 后台管理能力不足 | 高 | 仍待修复 | Sprint-05: 管理后台 |
| 8 | Tauri 权限最小化 (仅 core:window) | 低 | **已压实** — 当前 7 项足够 | 后续功能需时再扩展 |
| 9 | 人工 GUI/E2E 验证缺口 | 中 | **部分压实** — runbook 已就绪，自动化全覆盖 | 用户按 runbook 手动执行 |
| 10 | 月度积分发放调度器未实现 | 中 | 仍待修复 | Sprint-05: cron 调度器 |
| 11 | Provider 无熔断器/健康检查 | 中 | 仍待修复 | Sprint-05: Provider 运维增强 |
| 12 | 余额不足 402 UX | 低 | 仍待优化 — 402 正确返回但无充值引导 | Sprint-05: 桌面端充值引导 |

### 统计

- **已压实/缓解**: 2/12（#2 NSIS 网络、#8 Tauri 权限）
- **部分压实**: 1/12（#9 GUI 缺口 — runbook 就绪但未人工执行）
- **仍待修复**: 9/12

## 当前自动化验证基线

- 后端回归: **293 passed, 74 skipped**（2026-06-02）
- 前端构建: **74 modules, 0 errors**
- Tauri release build: **EXE + MSI + NSIS 生成成功**
- `git diff --check`: **通过**
