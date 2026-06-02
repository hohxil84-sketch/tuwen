# S04-T09: Tauri 内测品牌图标替换

## 状态

`COMPLETED`

## 分支

`feature/sprint-04-task-09-tauri-brand-icon`

## 完成摘要

已将 Tauri 默认占位图标替换为内测品牌图标（暗色背景 + 几何 "A" 字标识 + 双色渐变）。`icon.ico`（7 尺寸 16–256 px）+ `icon.png`（128×128 RGBA），均由 Pillow 生成。`tauri.conf.json` 图标引用未变。`npm run build`（74 modules, 0 errors）和 `npm run tauri build`（EXE + MSI 生成成功，NSIS 网络超时与图标无关）均已验证。详细记录见 PROGRESS.md 和模块上下文。

## 背景

S04-T07 已恢复 Tauri 2 桌面工程源配置，S04-T08 已完成本地 EXE / MSI / NSIS 打包 smoke 验证。当前 `desktop-app/src-tauri/icons/` 仍使用 Tauri 默认占位图标，打包产物和 Windows 应用图标缺少项目识别度。

本任务只做内测阶段的最小品牌图标替换：用一个可辨识、可打包、可回滚的 MVP 图标替换默认占位图标，并记录图标来源、格式、构建验证和限制。

## 用户目标

为后续 Windows 内测分发准备一个不再显示 Tauri 默认图标的桌面应用图标。由于用户尚未提供正式品牌 VI，本任务按保守拆解执行：只做内测可用图标，不做最终品牌体系设计。

## What To Build

- 设计或生成一个简单、清晰、适合内测的应用图标，表达“AI 图文广告助手 / AdAssistant”身份。
- 替换或补齐 `desktop-app/src-tauri/icons/` 下 Tauri 打包需要的图标文件。
- 保持 `tauri.conf.json` 的图标引用与实际文件一致。
- 运行桌面端构建和 Tauri 打包，确认新图标不会破坏 EXE / MSI / NSIS 生成。
- 更新 `docs/17-release-and-update.md`，把“占位图标”状态改为“内测图标已替换”，同时保留正式品牌图标仍待确认的限制。
- 新增 `docs/module-context/sprint-04-task-09-tauri-brand-icon/context.md`，记录图标文件、设计说明、验证结果、残余风险和回滚方式。
- 追加更新 `PROGRESS.md`。

## What Not To Build

- 不做正式品牌 VI、商标、logo 体系或版权注册。
- 不做官网、营销页、宣传物料或应用内 UI 大改版。
- 不做正式发布、上传、分发或安装包签名。
- 不配置 updater endpoint、签名私钥、代码签名证书或发布通道。
- 不修改 Tauri capabilities、sidecar、本地 Python 服务启动方式或文件系统权限。
- 不修改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment、Billing 或 CI。
- 不新增真实 AI Provider 调用、扣费逻辑或客户端授权逻辑。
- 不提交 `desktop-app/src-tauri/target/**`、`desktop-app/dist/**`、EXE、MSI、NSIS 安装包或构建日志。

## Allowed Files

- `desktop-app/src-tauri/icons/**`
- `desktop-app/src-tauri/tauri.conf.json`（仅当图标文件名或格式变化需要同步引用）
- `docs/17-release-and-update.md`
- `docs/09-desktop-app-guide.md`（仅当需要补充图标验证说明）
- `docs/module-context/sprint-04-task-09-tauri-brand-icon/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，必须先暂停并请求用户或 Codex 更新任务单。不得用“顺手修复”扩大范围。

## Forbidden Files

- `desktop-app/src-tauri/target/**`
- `desktop-app/dist/**`
- `desktop-app/src-tauri/gen/schemas/**`
- `desktop-app/src/**`（除非用户另行确认应用内 UI 图标同步任务）
- `desktop-app/local-service/**`
- `cloud-backend/**`
- `shared/**`
- `official-website/**`
- `.github/**`
- 根目录 `package.json`
- 根目录 `package-lock.json`
- 数据库 DDL / migrations
- Provider、Auth、Credit、Payment、Billing 相关文件
- 任何真实密钥、证书、签名私钥、生产连接串或发布凭据

## Dependency Permission

默认不允许新增依赖。

允许使用本机已有工具、Tauri 现有官方依赖、Rust / Node 项目中已经安装的依赖生成或验证图标。若需要安装新的图标生成工具、字体、图片处理库、系统级工具或 npm / Python / Rust 依赖，必须暂停并请求用户确认。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：Tauri 图标会进入桌面打包产物，属于发布链路前置工作。本任务只授权图标资源替换和本地打包验证，不授权正式发布、签名、上传、updater、CI 或权限变更。

仍需暂停确认的情况：

- 需要使用第三方受版权限制的图标、商标、字体或素材。
- 需要新增依赖、安装系统级工具或下载外部资产。
- 需要修改 CI / GitHub Actions / deployment。
- 需要配置代码签名证书、publisher、timestamp server、签名私钥或正式发布身份。
- 需要新增 updater、发布通道、下载地址或远程更新逻辑。
- 需要扩大 Tauri capabilities 或新增 Tauri 插件。
- 需要修改应用内 UI、后端、数据库、shared DTO、Provider、Auth、Credit 或 Payment。
- 需要删除文件、重命名目录或大规模重构。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串、证书或签名私钥。
- 不把 Provider API Key 放入客户端。
- 不新增 updater endpoint 或远程下载执行逻辑。
- 不扩大 Tauri capabilities。
- 不提交构建产物、安装包、EXE、日志或本地缓存。
- 不引入来源不明、授权不清的第三方图标、字体或图片素材。
- 文档中只记录图标相对路径、格式、来源说明和验证结果，不复制二进制内容。

## Acceptance Criteria

- [ ] `desktop-app/src-tauri/icons/` 不再使用 Tauri 默认占位图标。
- [ ] 图标在小尺寸下仍可辨识，至少覆盖 Windows 打包所需的 `.ico` 和 Tauri 配置引用的 `.png`。
- [ ] `desktop-app/src-tauri/tauri.conf.json` 的 `bundle.icon` 引用与实际图标文件一致。
- [ ] `npm run build` 在 `desktop-app` 下通过。
- [ ] `npm run tauri build` 在 `desktop-app` 下通过，或记录明确失败原因且失败与本任务无关。
- [ ] 如打包成功，记录新图标对应的 EXE / MSI / NSIS 产物相对路径；不提交产物。
- [ ] 文档已说明当前图标是内测图标，不代表最终品牌 VI。
- [ ] 未新增依赖、未下载授权不明外部素材、未写入 secrets。
- [ ] 未修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment、CI 或 Tauri capabilities。
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

如 `npm run tauri build` 成功，必须记录：

- `desktop-app/src-tauri/target/release/ad-assistant-desktop.exe`
- `desktop-app/src-tauri/target/release/bundle/msi/*.msi`
- `desktop-app/src-tauri/target/release/bundle/nsis/*setup.exe`

建议人工验证：

- 启动生成的 EXE 或 installer 安装后的应用。
- 确认 Windows 任务栏 / 窗口 / 安装包显示不再是 Tauri 默认图标。
- 确认主窗口能打开，深色 frameless 标题栏和窗口控制按钮仍正常。

## Rollback Plan

- revert 本任务 commit 可恢复上一版图标和文档记录。
- 如只需回退图标，恢复 `desktop-app/src-tauri/icons/` 中上一版 `icon.ico` 和 `icon.png`，并确认 `tauri.conf.json` 图标引用不变。
- 本任务不涉及数据库迁移、远端发布或用户数据变更，无数据回滚步骤。
- 本地生成的 `target/**`、`dist/**`、EXE、MSI 或 NSIS 产物不得提交；清理前必须确认路径位于 `desktop-app/` 构建输出目录内。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 图标设计/来源说明
- 图标文件格式和相对路径
- `tauri.conf.json` 图标引用是否变化
- 生成产物路径和文件类型，或失败阻塞原因
- 人工图标验证结果（如已执行）
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
