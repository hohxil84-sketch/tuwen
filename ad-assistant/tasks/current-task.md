# S04-T07: Tauri 工程源配置初始化与深色标题栏恢复

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 分支

`feature/sprint-04-task-07-tauri-source-init`

## 完成摘要

S04-T07 已完成：手动创建 Tauri 2 源配置 10 个文件，frameless 窗口 + AppTopbar 自定义深色标题栏（拖拽区 + 窗口控制按钮），capabilities 最小化 7 项权限。npm run build 74 modules 0 errors，tauri dev exit 0，Cargo 355 crates 编译通过，desktop-app.exe 成功启动。vite.config.ts 额外修改（忽略 target/）属 Tauri 运行必要配置。

## 背景

S04-T06 已审计 `desktop-app/src-tauri/`，确认当前仅有 `.gitkeep` 和 `target/` 构建产物，不存在可提交的 Tauri 源配置文件：

- `desktop-app/src-tauri/tauri.conf.json` 或 `tauri.conf.json5`
- `desktop-app/src-tauri/Cargo.toml`
- `desktop-app/src-tauri/src/main.rs`
- `desktop-app/src-tauri/src/lib.rs`
- `desktop-app/src-tauri/capabilities/*.json`

因此 S04-T06 已标记为 `BLOCKED_NEEDS_TAURI_SOURCE`，未能处理 Windows / Tauri 原生白色标题栏与深色桌面 UI 不一致的问题。

本任务目标是补齐最小可维护的 Tauri 2 源配置，让桌面端重新具备可运行的 Tauri 工程基础，并在该基础上实现深色标题栏或等效的深色窗口 chrome 最小修复。

## 用户目标

恢复桌面端 Tauri 工程源配置，使 `desktop-app` 能以 Tauri 桌面应用方式运行；同时解决或最小化顶部白色系统标题栏破坏深色 UI 观感的问题。

## What To Build

- 初始化或恢复 `desktop-app/src-tauri/` 下可提交的 Tauri 2 源配置文件。
- 补齐 Tauri 运行所需的最小 Rust 入口、配置文件和 capabilities。
- 在不扩大权限的前提下配置窗口外观，使标题栏 / 系统 chrome 与现有深色工作台尽量一致。
- 如采用 `decorations: false`、frameless 或自定义标题栏，必须同时提供可用的拖拽区域和窗口控制能力，且不破坏现有页面布局。
- 补齐或修正 `desktop-app/package.json` 中 Tauri 开发脚本和官方依赖。
- 更新 `docs/module-context/sprint-04-task-07-tauri-source-init/context.md`，记录初始化方式、关键配置、权限边界、验证结果、风险和回滚方式。
- 追加更新 `PROGRESS.md`。

## What Not To Build

- 不做 EXE packaging。
- 不生成安装包。
- 不新增自动更新能力。
- 不发布版本。
- 不接入真实 Provider。
- 不修改后端 API、数据库、shared DTO、Auth、Credit、Payment 或 Provider 逻辑。
- 不修改本地 OCR 服务启动方式。
- 不改 Dashboard 业务布局、业务卡片、路由功能或页面数据逻辑，除非自定义标题栏必须做最小壳层适配。
- 不修改或提交 `desktop-app/src-tauri/target/**`。

## Allowed Files

- `desktop-app/src-tauri/tauri.conf.json`
- `desktop-app/src-tauri/tauri.conf.json5`
- `desktop-app/src-tauri/Cargo.toml`
- `desktop-app/src-tauri/Cargo.lock`
- `desktop-app/src-tauri/src/main.rs`
- `desktop-app/src-tauri/src/lib.rs`
- `desktop-app/src-tauri/capabilities/*.json`
- `desktop-app/src-tauri/icons/**`（仅 Tauri 默认图标或项目已有图标的必要接入）
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `desktop-app/src/App.vue`（仅当窗口拖拽区或自定义标题栏需要最小适配）
- `desktop-app/src/components/dashboard/AppTopbar.vue`（仅当与页面顶部栏整合自定义标题栏时）
- `desktop-app/src/styles/**`（仅当已有样式体系需要最小标题栏样式补充）
- `docs/09-desktop-app-guide.md`
- `docs/26-desktop-dashboard-ui-redesign.md`
- `docs/module-context/sprint-04-task-07-tauri-source-init/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，且属于 Tauri 初始化的必要文件，必须先暂停并请求用户或 Codex 更新任务单。

## Forbidden Files

- `desktop-app/src-tauri/target/**`
- `cloud-backend/**`
- `shared/**`
- `desktop-app/local-service/**`
- `official-website/**`
- `.github/**`
- 根目录 `package.json`
- 根目录 `package-lock.json`
- 数据库 DDL / migrations
- Provider、Auth、Credit、Payment、Billing 相关文件
- 与 Tauri 初始化和标题栏无关的 Dashboard 业务逻辑

## Dependency Permission

本任务允许新增或恢复 Tauri 官方必要依赖，但仅限以下范围：

- `@tauri-apps/api`
- `@tauri-apps/cli`
- Rust 侧 Tauri 2 官方 crate 及其初始化所需依赖

禁止新增非 Tauri 官方依赖。禁止升级与本任务无关的前端、后端或根目录依赖。若 npm 或 Cargo 自动改动超出 Tauri 初始化必要范围，必须暂停说明原因并请求确认。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：本任务会恢复 Tauri 工程源配置，并可能修改桌面窗口 chrome、Tauri capabilities、依赖和 lockfile。这些属于高风险边界，但本任务单已明确限定允许范围和验收要求。

仍需暂停确认的情况：

- 需要扩大 Tauri capabilities 权限到文件系统、shell、网络白名单或远程执行。
- 需要修改本地 Python 服务启动、sidecar、打包配置或 updater。
- 需要修改 CI、Docker、部署或环境变量契约。
- 需要删除文件、重命名目录或大规模重构。
- 需要修改后端、数据库、shared DTO、Provider、Auth、Credit 或 Payment。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串或用户隐私数据。
- 不把 Provider API Key 放入客户端。
- 不绕过云端授权、设备绑定、套餐权限或扣费链路。
- Tauri capabilities 必须最小化，只允许应用当前运行所需权限。
- 不新增 shell、filesystem、remote execution、全局网络访问等高风险能力，除非用户另行确认。
- 不修改 `target/**` 构建产物。

## Acceptance Criteria

- [ ] `desktop-app/src-tauri/` 下存在可提交的 Tauri 2 源配置文件，而不只是 `.gitkeep` 和 `target/**`。
- [ ] `desktop-app/package.json` 包含可运行的 Tauri 开发脚本和必要官方依赖。
- [ ] `npm run build` 在 `desktop-app` 下通过。
- [ ] 如果本机 Rust / Tauri 环境可用，`npm run tauri dev` 能启动桌面应用。
- [ ] 如果 `npm run tauri dev` 因本机环境不可用失败，必须记录缺失环境、失败原因和替代验证。
- [ ] 标题栏 / 系统 chrome 已采用深色或等效方案；若平台限制导致不能完全深色化，必须记录原因和可接受降级。
- [ ] 如采用 frameless / 自定义标题栏，窗口拖拽、关闭、最小化、最大化仍可用。
- [ ] 未修改或提交 `desktop-app/src-tauri/target/**`。
- [ ] 未修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment、CI 或根目录依赖。
- [ ] 模块上下文已更新。
- [ ] `PROGRESS.md` 已追加记录。
- [ ] `git diff --check` 通过。

## Test Method

必须运行：

```powershell
cd ad-assistant/desktop-app
npm run build
```

必须运行：

```powershell
git diff --check
```

如果 Tauri 环境可用，必须运行：

```powershell
cd ad-assistant/desktop-app
npm run tauri dev
```

如果 `npm run tauri dev` 不可用，执行者必须提供：

- 本机缺失的具体工具或错误信息。
- `desktop-app/src-tauri/` 源文件清单。
- `package.json` Tauri 脚本和依赖检查结果。
- `npm run build` 结果。
- 未修改 `target/**` 的说明。

## Rollback Plan

- revert 本任务 commit 可移除 Tauri 源配置、依赖和标题栏适配。
- 如果只需要回滚标题栏方案，可恢复 `tauri.conf.*` 的窗口配置和相关 Vue/CSS 最小适配。
- 本任务不涉及数据库迁移或远端数据变更，无数据回滚步骤。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- Tauri 源配置初始化方式
- 标题栏 / 窗口 chrome 方案
- capabilities 权限清单和是否最小化
- 新增或恢复的依赖
- 未实现内容
- 测试命令和结果
- `npm run tauri dev` 人工验证结果或未验证原因
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
