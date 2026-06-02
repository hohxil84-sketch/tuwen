# S04-Closeout: Sprint-04 收尾总结与 Sprint-05 候选规划

## 状态

`COMPLETED`

## 分支

`docs/sprint-04-closeout`

## 完成摘要

- 新增 `docs/sprint-04-summary.md`，按 Sprint-01/02/03 风格完整覆盖 S04-T01 至 S04-T10 + 4 个规则增强
- 汇总当前能力（Provider 可靠性、Dashboard 数据集成、OCR 隐私清理、会员/套餐/充值、快捷入口接线、Tauri 桌面端）
- 记录 12 项残余风险（未签名、NSIS 网络、品牌 VI、CSS 阴影≠原生、模拟支付无风控、无 RBAC、后台不足等）
- 列出 Sprint-05 5 组候选方向（内测分发准备→基础后台→商业链路→E2E 验证→P1 功能探索）
- 未修改业务代码、后端、数据库、shared DTO、Tauri 权限、依赖或 CI
- `PROGRESS.md` 已追加 closeout 记录

## 背景

Sprint-04 已完成多个核心收口任务：Provider 可靠性、Dashboard 数据集成、OCR 历史清理、会员/套餐/充值、快捷入口接线、Tauri 工程恢复、深色 frameless 标题栏、本地打包 smoke、内测品牌图标、窗口边界视觉优化。

当前还没有 `docs/sprint-04-summary.md`。在启动 Sprint-05 前，需要先把 Sprint-04 的已完成能力、测试证据、残余风险和下一阶段候选整理成权威 summary，避免后续任务从零散 `PROGRESS.md` 条目里猜测项目状态。

## 用户目标

明确 Sprint-04 到底完成了什么、还剩哪些风险、Sprint-05 可以从哪些方向开始。本文档任务只做收尾和规划，不开发新功能，不启动 Sprint-05 实现。

## What To Build

- 新增 `docs/sprint-04-summary.md`，按 Sprint-01/02/03 summary 风格整理 Sprint-04。
- 汇总 Sprint-04 已完成模块，至少覆盖：
  - S04-T01 Provider Reliability / 预扣检查 + fallback/retry
  - S04-T02 Dashboard 数据集成 + AI 文案生成入口
  - S04-T03 Local OCR History Cleanup
  - S04-T04 会员/套餐/充值/管理员赠送额度
  - S04-T05 桌面端快捷入口接入已有真实功能
  - S04-T06 Tauri 深色标题栏审计
  - S04-T07 Tauri 工程源配置初始化与深色标题栏恢复
  - S04-T08 Tauri 打包与 EXE Smoke 验证
  - S04-T09 Tauri 内测品牌图标替换
  - S04-T10 Tauri frameless 窗口边界与阴影最小优化
- 汇总当前能力：云端 AI/扣费、会员充值、桌面 Dashboard、OCR、本地历史、Tauri 打包、内测桌面外观。
- 汇总残余风险：未签名安装包、NSIS 下载/网络不稳定、正式品牌 VI 未确认、原生窗口阴影未接入、模拟支付无风控、管理员白名单无 RBAC、后台管理能力不足、人工 GUI/E2E 验证缺口。
- 列出 Sprint-05 候选方向，并按建议优先级分组：
  - 内测分发准备
  - 基础后台 / 管理端
  - 商业链路加固
  - 端到端 smoke / 回归验证
  - P1 功能探索（需用户确认）
- 更新 `tasks/current-task.md` 完成后状态。
- 追加更新 `PROGRESS.md`，记录本次 closeout 文档任务。

## What Not To Build

- 不开发任何业务功能。
- 不启动 Sprint-05 具体实现。
- 不修改桌面端、后端、shared DTO、数据库、Provider、Auth、Credit、Payment 或 CI。
- 不新增依赖。
- 不创建后台页面、管理接口、支付接口或真实发布能力。
- 不做代码签名、updater、发布上传、安装包分发或 Docker/CI 变更。
- 不修改 S04 已完成任务的业务代码或测试代码。
- 不把未验证的内容写成已完成事实；不确定项必须标为残余风险或待验证。

## Allowed Files

- `docs/sprint-04-summary.md`
- `docs/13-module-roadmap.md`（仅当需要补充 Sprint-05 候选说明，且不得把 P1/BACKLOG 改成已启动）
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，必须先暂停并请求用户或 Codex 更新任务单。

## Forbidden Files

- `desktop-app/**`
- `cloud-backend/**`
- `shared/**`
- `official-website/**`
- `.github/**`
- `docs/module-context/**`（除非用户要求补某个模块上下文）
- `docs/sprint-01-summary.md`
- `docs/sprint-02-summary.md`
- `docs/sprint-03-summary.md`
- 数据库 DDL / migrations
- Provider、Auth、Credit、Payment、Billing 相关代码
- 任何真实密钥、证书、签名私钥、生产连接串或发布凭据

## Dependency Permission

不允许新增依赖。

本任务是纯文档任务，不允许安装、下载或引入任何 npm、Python、Rust、系统工具或外部资产。

## Major Change Status

`NO_MAJOR_CHANGE_EXPECTED`

原因：本任务只新增/更新规划文档和进度记录，不修改代码、依赖、API、数据库、Tauri 权限、CI 或发布链路。

必须暂停确认的情况：

- 需要修改代码、数据库、API contract、shared DTO、Provider、Auth、Credit、Payment 或 CI。
- 需要把 P1/BACKLOG/FUTURE 功能改为已启动。
- 需要创建 Sprint-05 的具体业务实现任务而不是 closeout summary。
- 发现 Sprint-04 某项完成状态与 `PROGRESS.md`、任务单或模块上下文冲突，且无法从本地文档判断。
- 需要删除文件、重命名目录或改动历史 summary。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串、证书或签名私钥。
- 不复制构建产物、安装包、日志或本地缓存内容。
- 不把未脱敏的用户数据、OCR 内容、支付数据或设备标识写入文档。
- 不把未验证的发布、安全或支付能力描述为已完成。
- Sprint-05 候选必须保持边界：P1 功能需用户确认，BACKLOG/FUTURE 仍禁止。

## Acceptance Criteria

- [ ] `docs/sprint-04-summary.md` 已新增，结构清晰并能独立说明 Sprint-04 状态。
- [ ] Sprint-04 已完成模块覆盖 S04-T01 至 S04-T10。
- [ ] 当前能力、测试证据、安全边界和残余风险均有记录。
- [ ] Sprint-05 候选方向已列出，且未把候选误写为已启动任务。
- [ ] P1/BACKLOG/FUTURE 边界未被放宽。
- [ ] 未修改业务代码、后端、数据库、shared DTO、Tauri 权限、依赖或 CI。
- [ ] `PROGRESS.md` 已追加 closeout 记录。
- [ ] `tasks/current-task.md` 完成后只做状态类最小更新。
- [ ] `git diff --check` 通过。

## Test Method

必须运行：

```powershell
git diff --check
```

必须检查：

```powershell
git status --short --branch
```

建议检查：

```powershell
rg -n "S04-T|Sprint-05|BACKLOG|FUTURE|MVP_OPTIONAL" docs/sprint-04-summary.md docs/13-module-roadmap.md PROGRESS.md tasks/current-task.md
```

本任务不需要运行前端、后端或 Tauri 构建测试，因为不修改代码。

## Rollback Plan

- revert 本任务 commit 可移除 Sprint-04 closeout 文档和进度记录。
- 如只需回退 summary，删除 `docs/sprint-04-summary.md` 并恢复 `PROGRESS.md` 与 `tasks/current-task.md` 的本任务记录。
- 本任务不涉及数据库迁移、依赖、发布、构建产物或用户数据变更，无数据回滚步骤。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- Sprint-04 summary 覆盖范围
- Sprint-05 候选方向
- 明确未启动的内容
- 测试命令和结果
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
