# S04-R01: Sprint-04 内测 E2E Smoke 与残余风险压实

## 状态

`COMPLETED`

## 分支

`risk/sprint-04-e2e-smoke`

## 完成摘要

- 新增 `docs/28-sprint-04-e2e-smoke.md`：完整 E2E smoke runbook（5/6 自动化 PASS、7/7 静态验证 PASS、3/5 打包产物 PASS、8/8 GUI 链路 NOT_RUN 附带手动复现步骤）
- 新增 `docs/sprint-04-summary.md`：残余风险跟踪版（12 项风险 E2E 压实状态，2 项已缓解、1 项部分压实、9 项仍待修复）
- 后端全量回归：293 passed, 74 skipped
- 前端构建：74 modules, 0 errors
- Tauri release build：EXE + MSI + NSIS 生成成功
- 未修改业务代码、测试代码、数据库、shared DTO、Tauri 权限、依赖或 CI
- 新发现缺陷：0
- `PROGRESS.md` 已追加记录

## 背景

Sprint-04 closeout 已记录 12 项残余风险，其中最适合优先处理的是“人工 GUI/E2E 验证缺口”：S04-T07 至 S04-T10 主要通过前端构建、Tauri 编译和静态检查验证，缺少真实 Windows 桌面环境下的完整内测 smoke。

相比代码签名、RBAC、真实支付风控、Windows 原生 DWM 阴影等高风险改造，E2E smoke 不需要改业务代码，也能先确认现有能力是否真的可交付。它可以把“已知风险”拆成：已验证通过、环境阻塞、真实缺陷、后续专项任务。

## 用户目标

先把 Sprint-04 的残余风险压实：通过一轮可复现的内测 E2E smoke 验证，确认当前桌面应用从安装/启动到核心业务链路是否可用，并把未通过项明确记录为后续修复任务。

## What To Build

- 新增 Sprint-04 内测 E2E smoke runbook，覆盖准备环境、启动服务、创建/准备测试用户、桌面端运行、核心链路验证和结果记录。
- 运行或指导运行现有验证命令，至少覆盖：
  - 后端回归或关键聚焦测试
  - 桌面端 `npm run build`
  - Tauri dev 或 Tauri build 验证
  - `git diff --check`
- 验证并记录核心链路：
  - 登录/设备绑定
  - Dashboard 数据加载
  - OCR 上传、结果展示、历史记录
  - AI 文案生成
  - 会员/套餐/充值记录
  - OCR 历史删除/清空
  - Tauri 窗口启动、拖拽、最小化、最大化/还原、关闭
  - 打包产物启动或安装后的 Smoke（如环境允许）
- 将验证结果分为 `PASS` / `FAIL` / `BLOCKED_BY_ENV` / `NOT_RUN`。
- 对失败项必须记录现象、复现步骤、可能归因、建议后续任务，不做猜测式修复。
- 更新 `docs/sprint-04-summary.md` 的残余风险状态，把已验证的风险标注为已压实或仍待修复。
- 追加更新 `PROGRESS.md`。

## What Not To Build

- 不修复本轮发现的业务缺陷；缺陷只记录根因线索和后续任务建议。
- 不做代码签名、证书申请、SmartScreen 绕过或安装包发布。
- 不接入 Windows DWM API、Tauri window-shadows 插件、透明窗口、Mica 或 Acrylic。
- 不实现 RBAC、管理员后台、审计日志或权限体系。
- 不接入真实支付、支付回调验签、订单状态机、充值风控或月度积分调度器。
- 不修改 Provider 路由、真实 AI 调用、扣费算法、套餐规则或 API contract。
- 不修改数据库 DDL / migrations。
- 不新增依赖，不修改 lockfile，不修改 CI。
- 不提交构建产物、安装包、EXE、日志、本地 SQLite 数据库或缓存。

## Allowed Files

- `docs/28-sprint-04-e2e-smoke.md`
- `docs/sprint-04-summary.md`
- `docs/09-desktop-app-guide.md`（仅当需要补充 E2E runbook 入口）
- `docs/11-cloud-backend-guide.md`（仅当需要补充 E2E runbook 入口）
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，必须先暂停并请求用户或 Codex 更新任务单。

## Forbidden Files

- `desktop-app/src/**`
- `desktop-app/src-tauri/**`
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `cloud-backend/app/**`
- `cloud-backend/tests/**`
- `cloud-backend/pyproject.toml`
- `cloud-backend/requirements*.txt`
- `shared/**`
- `official-website/**`
- `.github/**`
- 数据库 DDL / migrations
- Provider、Auth、Credit、Payment、Billing 相关代码
- 任何真实密钥、证书、签名私钥、生产连接串或发布凭据

## Dependency Permission

不允许新增依赖。

允许使用项目现有依赖、现有脚本、现有本地服务和现有测试命令。若验证需要下载新工具、安装系统组件、改 lockfile、配置 Docker 或访问外部服务，必须暂停并请求用户确认。

## Major Change Status

`NO_MAJOR_CHANGE_EXPECTED`

原因：本任务是验证和风险压实任务，预期只新增/更新 runbook、summary 和进度记录，不修改业务代码、依赖、API、数据库、Tauri 权限、CI 或发布链路。

必须暂停确认的情况：

- 需要修改代码来通过 smoke。
- 需要新增依赖、安装系统工具、修改 lockfile 或改 CI。
- 需要真实支付、真实发布、代码签名证书、生产 API Key 或生产连接串。
- 需要修改数据库 DDL / migrations、API contract、shared DTO、Provider、Auth、Credit 或 Payment。
- 需要删除文件、清空数据、迁移用户数据或提交构建产物。
- 发现阻塞缺陷需要修复，且修复超出纯文档/验证范围。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串、证书或签名私钥。
- 不记录未脱敏的用户数据、OCR 内容、支付信息、设备指纹或测试 token。
- E2E smoke 使用本地测试用户、本地测试数据或明确标注的 mock/simulated 数据。
- 不绕过授权、设备绑定、余额检查或管理员权限。
- 不提交构建产物、安装包、EXE、日志、本地 DB 或缓存。

## Acceptance Criteria

- [ ] `docs/28-sprint-04-e2e-smoke.md` 已新增，包含可复现步骤和结果表。
- [ ] 核心链路验证项均被标记为 `PASS` / `FAIL` / `BLOCKED_BY_ENV` / `NOT_RUN`。
- [ ] 对所有 `FAIL` 和 `BLOCKED_BY_ENV` 项记录复现步骤、现象、归因线索和后续任务建议。
- [ ] `docs/sprint-04-summary.md` 已更新残余风险状态，未把未验证项写成已解决。
- [ ] 未修改业务代码、测试代码、数据库、shared DTO、Tauri 权限、依赖或 CI。
- [ ] 未提交构建产物、安装包、日志、本地 DB 或缓存。
- [ ] `PROGRESS.md` 已追加本任务记录。
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

建议按 runbook 尽量运行：

```powershell
cd ad-assistant/cloud-backend
python -m pytest tests/ -v
```

```powershell
cd ad-assistant/desktop-app
npm run build
```

```powershell
cd ad-assistant/desktop-app
npm run tauri dev
```

```powershell
cd ad-assistant/desktop-app
npm run tauri build
```

如果某些命令因本地环境、GUI、网络或系统工具限制无法运行，必须在 runbook 中标为 `BLOCKED_BY_ENV` 并记录具体原因。

## Rollback Plan

- revert 本任务 commit 可移除 E2E smoke runbook、summary 更新和进度记录。
- 本任务不涉及数据库迁移、依赖、业务代码、发布或用户数据变更，无数据回滚步骤。
- 如验证过程生成本地 `dist/**`、`target/**`、EXE、MSI、NSIS、日志或数据库文件，不得提交；清理前必须确认路径位于项目构建输出或本地运行数据目录内。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 实际运行的验证命令和结果
- E2E smoke 覆盖范围
- `PASS` / `FAIL` / `BLOCKED_BY_ENV` / `NOT_RUN` 汇总
- 新发现缺陷或环境阻塞
- 明确未修复的残余风险
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
