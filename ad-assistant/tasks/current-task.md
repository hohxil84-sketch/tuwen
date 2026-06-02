# S04-T08: Tauri 打包与 EXE Smoke 验证

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 分支

`feature/sprint-04-task-08-tauri-package-smoke`

## 完成摘要

Tauri 本地打包 Smoke 验证通过。`bundle.active` 开启 + `targets: "all"`，`npm run tauri build` 成功生成裸 EXE + MSI + NSIS 安装包。`productName` 修正为 ASCII "AdAssistant"（WiX v3 codepage 1252 不兼容中文）。构建产物未提交，待用户人工 GUI 验证（窗口启动、深色标题栏、窗口控制按钮）。详细记录见 PROGRESS.md 和模块上下文。

## 背景

S04-T07 已恢复 `desktop-app/src-tauri/` 的 Tauri 2 源配置，并完成 frameless 深色标题栏方案。当前 `desktop-app` 已具备 `npm run tauri dev` 开发模式，但 `tauri.conf.json` 中 `bundle.active` 仍为 `false`，尚未验证能否生成本地 Windows EXE / installer 构建产物。

本任务目标是做一次最小的 Tauri packaging smoke：开启必要 bundle 配置，运行本地构建，确认是否能生成可启动的 Windows 桌面产物，并记录构建产物路径、验证方式、失败原因或后续阻塞项。

## 用户目标

确认当前桌面端是否已经具备生成本地 EXE / 安装包的基础能力，为后续内测分发做准备；本任务只做本地打包验证，不做正式发布。

## What To Build

- 配置最小 Tauri bundle，使 `npm run tauri build` 能尝试生成 Windows 桌面构建产物。
- 如果现有图标、identifier、productName、version、bundle 配置不满足打包要求，在最小范围内修正。
- 运行 Tauri packaging smoke，确认生成的 `.exe` 或 installer 产物是否存在。
- 对生成产物做最小人工验证：能启动应用主窗口，且深色标题栏 / 自定义窗口控制按钮仍可见。
- 更新 `docs/17-release-and-update.md`，记录当前本地打包 smoke 流程和限制。
- 新增 `docs/module-context/sprint-04-task-08-tauri-package-smoke/context.md`，记录 bundle 配置、产物路径、验证结果、残余风险和回滚方式。
- 追加更新 `PROGRESS.md`。

## What Not To Build

- 不做正式发布。
- 不上传、分发或签名安装包。
- 不新增自动更新能力。
- 不配置 updater endpoint、签名私钥或发布通道。
- 不做代码签名证书接入。
- 不做 MSI / NSIS 深度定制主题。
- 不接入 sidecar。
- 不修改本地 Python 服务启动方式。
- 不修改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment 或 CI。
- 不修改业务页面、路由、Provider 调用、扣费逻辑或登录授权逻辑。
- 不提交 `desktop-app/src-tauri/target/**`、`desktop-app/dist/**` 或任何构建产物。

## Allowed Files

- `desktop-app/src-tauri/tauri.conf.json`
- `desktop-app/src-tauri/Cargo.toml`（仅当 Tauri build 明确要求最小 metadata 修正）
- `desktop-app/src-tauri/icons/**`（仅当现有图标格式导致打包失败，且只允许替换/补齐应用图标）
- `desktop-app/package.json`（仅当需要新增 `tauri:build` 这类脚本别名）
- `desktop-app/package-lock.json`（仅当 npm 脚本或 Tauri 官方依赖的必要修正导致 lockfile 更新）
- `docs/17-release-and-update.md`
- `docs/09-desktop-app-guide.md`
- `docs/module-context/sprint-04-task-08-tauri-package-smoke/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，且属于 Tauri packaging 的必要文件，必须先暂停并请求用户或 Codex 更新任务单。

## Forbidden Files

- `desktop-app/src-tauri/target/**`
- `desktop-app/dist/**`
- `desktop-app/src-tauri/gen/schemas/**`
- `cloud-backend/**`
- `shared/**`
- `desktop-app/local-service/**`
- `official-website/**`
- `.github/**`
- 根目录 `package.json`
- 根目录 `package-lock.json`
- 数据库 DDL / migrations
- Provider、Auth、Credit、Payment、Billing 相关文件
- 任何真实密钥、证书、签名私钥、生产连接串或发布凭据

## Dependency Permission

默认不允许新增依赖。

已允许使用现有 Tauri 官方依赖：

- `@tauri-apps/api`
- `@tauri-apps/cli`
- Rust 侧已存在的 Tauri 2 crates

如果 `npm run tauri build` 要求安装 Windows 打包工具、Rust target、WiX、NSIS 或系统级工具，执行者必须先报告缺失项、安装来源建议、风险和替代验证方式；不得在任务内自行安装系统工具，除非用户明确确认。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：Tauri packaging、bundle 配置、安装包生成和产物验证属于发布链路前置工作，是高风险边界。本任务单只确认本地 packaging smoke，不允许发布、签名、上传、自动更新或改 CI。

仍需暂停确认的情况：

- 需要配置代码签名证书、私钥、publisher、timestamp server 或正式发布身份。
- 需要新增 updater、发布通道、下载地址或远程更新逻辑。
- 需要修改 CI / GitHub Actions / deployment。
- 需要接入 sidecar 或修改本地 Python 服务启动方式。
- 需要新增 Tauri 插件或扩大 capabilities 权限。
- 需要修改后端、数据库、shared DTO、Provider、Auth、Credit 或 Payment。
- 需要安装系统级打包工具。
- 需要删除文件、重命名目录或大规模重构。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串、证书或签名私钥。
- 不把 Provider API Key 放入客户端。
- 不新增 updater endpoint 或远程下载执行逻辑。
- 不扩大 Tauri capabilities。
- 不提交构建产物、安装包、EXE、日志或本地缓存。
- 不修改客户端 token 存储策略。
- 打包产物如需记录路径，只写入相对路径和文件名，不复制二进制内容。

## Acceptance Criteria

- [ ] `desktop-app/src-tauri/tauri.conf.json` 的 bundle 配置满足本地打包 smoke 要求。
- [ ] `npm run build` 在 `desktop-app` 下通过。
- [ ] `npm run tauri build` 已运行，并记录成功或失败结果。
- [ ] 如打包成功，记录生成的 EXE / installer 相对路径和文件类型。
- [ ] 如打包成功，人工启动产物并确认主窗口可打开、深色标题栏可见、窗口控制按钮可用。
- [ ] 如打包失败，记录精确失败原因、缺失工具、阻塞项和后续修复建议。
- [ ] 未提交 `desktop-app/src-tauri/target/**`、`desktop-app/dist/**`、installer、EXE 或日志。
- [ ] 未新增自动更新、代码签名、发布上传或 CI 改动。
- [ ] 未修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment。
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
cd ad-assistant/desktop-app
npm run tauri build
```

必须运行：

```powershell
git diff --check
```

如果 `npm run tauri build` 成功，必须人工验证：

- 启动生成的 EXE 或 installer 安装后的应用。
- 确认主窗口能打开。
- 确认 frameless 深色标题栏仍正常。
- 确认最小化、最大化/还原、关闭按钮可用。

如果 `npm run tauri build` 失败，执行者必须提供：

- 原始错误摘要。
- 缺失工具或配置项。
- 是否与本任务允许范围相关。
- 不安装系统工具时的替代验证结果。
- 后续任务建议。

## Rollback Plan

- revert 本任务 commit 可恢复打包配置和文档记录。
- 如果仅需关闭打包，恢复 `tauri.conf.json` 中 `bundle.active = false`。
- 本任务不涉及数据库迁移、远端发布或用户数据变更，无数据回滚步骤。
- 本地生成的 `target/**`、`dist/**`、EXE 或 installer 产物不得提交；清理前必须确认路径位于 `desktop-app/` 构建输出目录内。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- bundle 配置变化
- 生成产物路径和文件类型，或失败阻塞原因
- 人工启动验证结果
- 未实现内容
- 测试命令和结果
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
