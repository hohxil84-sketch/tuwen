# S04-T10: Tauri frameless 窗口边界与阴影最小优化

## 状态

`COMPLETED`

## 分支

`feature/sprint-04-task-10-tauri-window-depth`

## 完成摘要

已为 frameless 窗口增加最小 CSS 视觉边界：`App.vue` `#app-shell` 新增 1px 内描边 + 40px 柔和内阴影。纯 CSS 方案，未新增依赖，未修改 tauri.conf.json/Rust/capabilities。前端构建通过（74 modules, 0 errors）。此方案不等同于 Windows 原生窗口阴影，正式方案需 DWM API 或 Tauri 插件专项处理。详细记录见 PROGRESS.md 和模块上下文。

## 背景

S04-T07 已采用 `decorations: false` 的 frameless 窗口方案，解决了 Windows 系统标题栏与深色工作台不一致的问题。该方案的残余风险是：部分 Windows 版本下 frameless 窗口缺少原生系统阴影，窗口边界与桌面背景区分不够明显。

S04-T08 已验证本地打包链路，S04-T09 已替换内测图标。下一步适合做一个低风险桌面体验收口任务：在不引入新依赖、不扩大 Tauri 权限、不接入系统级插件的前提下，为当前 frameless 窗口补齐最小的视觉边界、内阴影或外观层次，并记录原生阴影仍需后续专项处理的边界。

## 用户目标

让内测桌面应用在 frameless 模式下更容易看出窗口边界，减少“窗口贴在桌面上没有层次”的观感问题。本任务只做最小 UI/CSS 级优化和验证，不做 Windows 原生阴影插件或系统 API 接入。

## What To Build

- 审查当前 `App.vue`、`AppTopbar.vue` 和 Tauri 窗口配置，确认 frameless 窗口边界感的主要来源。
- 在最小范围内增加窗口外壳的视觉边界，例如内描边、顶部/侧边分隔、柔和内阴影、最大化状态下的边界降级处理。
- 保持 Dashboard、OCR、会员中心、AI 文案页等现有页面布局不被压缩、遮挡或重新缩放。
- 浏览器开发模式和 Tauri 模式都应保持可用；浏览器模式不应出现多余窗口控制按钮。
- 更新 `docs/17-release-and-update.md`，说明当前采用的是 CSS/视觉层级缓解方案，不等同于 Windows 原生窗口阴影。
- 新增 `docs/module-context/sprint-04-task-10-tauri-window-depth/context.md`，记录方案、验证结果、限制和回滚方式。
- 追加更新 `PROGRESS.md`。

## What Not To Build

- 不接入 Windows 原生阴影插件、DWM API、native window shadow crate 或自定义 Rust 命令。
- 不新增 Tauri 插件或扩大 capabilities。
- 不开启透明窗口、毛玻璃、acrylic、mica 或系统级窗口特效。
- 不恢复系统标题栏，不改变 `decorations: false` 的当前方案。
- 不重做 Dashboard UI、导航、页面布局或主题系统。
- 不修改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment、Billing 或 CI。
- 不做正式发布、上传、分发、代码签名或 updater。
- 不提交 `desktop-app/src-tauri/target/**`、`desktop-app/dist/**`、EXE、MSI、NSIS 安装包或构建日志。

## Allowed Files

- `desktop-app/src/App.vue`
- `desktop-app/src/components/dashboard/AppTopbar.vue`（仅当标题栏边界或拖拽区视觉需要同步）
- `desktop-app/src-tauri/tauri.conf.json`（仅允许读取；若需要修改，必须先暂停并更新任务单）
- `docs/17-release-and-update.md`
- `docs/09-desktop-app-guide.md`（仅当需要补充窗口外观验证说明）
- `docs/module-context/sprint-04-task-10-tauri-window-depth/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

如执行过程中确认必须修改上述范围外文件，必须先暂停并请求用户或 Codex 更新任务单。

## Forbidden Files

- `desktop-app/src-tauri/target/**`
- `desktop-app/dist/**`
- `desktop-app/src-tauri/capabilities/**`
- `desktop-app/src-tauri/src/**`
- `desktop-app/src-tauri/Cargo.toml`
- `desktop-app/src-tauri/Cargo.lock`
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `desktop-app/src-tauri/gen/schemas/**`
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

不允许新增依赖。

不得安装、下载或引入新的 npm、Rust、Python、系统级窗口工具、Tauri 插件或图片处理库。只能使用现有前端 CSS、Vue 组件和现有 Tauri 配置进行验证。

## Major Change Status

`NO_MAJOR_CHANGE_EXPECTED`

原因：本任务预期只做桌面前端 CSS/视觉层级调整和文档记录，不修改 Tauri 权限、Rust 源码、依赖、后端、数据库、Provider、Auth、Credit、Payment、CI 或发布链路。

必须暂停确认的情况：

- 需要修改 `tauri.conf.json` 的 `transparent`、`decorations`、窗口尺寸、权限或安全配置。
- 需要新增 Tauri plugin、Rust crate、npm 依赖或系统级窗口阴影工具。
- 需要修改 `desktop-app/src-tauri/src/**`、capabilities、Cargo 文件或 lockfile。
- 需要接入 Windows DWM API、Mica、Acrylic、透明窗口或 native shadow 方案。
- 需要大规模改动 Dashboard 结构、路由、页面组件或主题变量。
- 需要修改后端、数据库、shared DTO、Provider、Auth、Credit 或 Payment。
- 需要删除文件、重命名目录或清理用户数据。

## Security Requirements

- 不写入真实 API Key、Token、密码、生产连接串、证书或签名私钥。
- 不新增 updater endpoint、远程下载执行逻辑或发布凭据。
- 不扩大 Tauri capabilities。
- 不新增本地文件系统、shell、http、clipboard、notification、global-shortcut 或 updater 权限。
- 不修改客户端 token 存储策略、授权流程、Provider 调用或扣费逻辑。
- 不提交构建产物、安装包、EXE、日志或本地缓存。

## Acceptance Criteria

- [ ] frameless 窗口在普通窗口尺寸下有清晰边界感，视觉上不再完全贴合桌面背景。
- [ ] 最大化状态下不出现不合理的外边距、裁切、滚动条或内容错位。
- [ ] 自定义标题栏拖拽区、最小化、最大化/还原、关闭按钮仍正常。
- [ ] Dashboard、OCR、History、Membership、AI 文案生成等主要页面不出现明显布局回归。
- [ ] 浏览器开发模式下布局仍正常，窗口控制按钮仍按现有逻辑隐藏。
- [ ] 未新增依赖、未修改 Tauri capabilities、未修改 Rust 源码、未修改 `package*.json` 或 `Cargo*`。
- [ ] 未修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment 或 CI。
- [ ] 文档已说明本任务是 CSS/视觉层级缓解，不是 Windows 原生阴影接入。
- [ ] 模块上下文已更新。
- [ ] `PROGRESS.md` 已追加记录。
- [ ] `npm run build` 通过。
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

建议运行：

```powershell
cd ad-assistant/desktop-app
npm run tauri dev
```

人工验证建议：

- 普通窗口尺寸：观察窗口四边、顶部标题栏和桌面背景之间是否有清晰层次。
- 最大化状态：确认没有多余外边距、内容裁切或滚动条异常。
- 标题栏：确认拖拽、最小化、最大化/还原、关闭按钮可用。
- 主要页面：快速切换 Dashboard、OCR、History、Membership、AI 文案生成，确认无明显布局回归。

如 `npm run tauri dev` 因环境或人工 GUI 限制无法完成，执行者必须记录原因，并至少完成 `npm run build`、静态 diff 审查和文档说明。

## Rollback Plan

- revert 本任务 commit 可恢复窗口外观和文档记录。
- 如只需回退视觉优化，恢复 `desktop-app/src/App.vue` 与 `AppTopbar.vue` 中本任务新增的样式。
- 本任务不涉及数据库迁移、远端发布、Tauri 权限、依赖或用户数据变更，无数据回滚步骤。
- 本地生成的 `dist/**`、`target/**` 或 Tauri 开发产物不得提交。

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- 窗口边界/阴影视觉方案说明
- 是否修改 `tauri.conf.json`
- 未实现内容，特别是是否仍未接入 Windows 原生阴影
- 测试命令和结果
- 人工验证结果（如已执行）
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
