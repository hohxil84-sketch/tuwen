# S04-T06: Tauri 深色标题栏审计与最小修复

## 状态

`BLOCKED_NEEDS_TAURI_SOURCE`

## 分支

`feature/sprint-04-task-06-tauri-dark-titlebar`

## 完成摘要

审计完毕：`desktop-app/src-tauri/` 仅含 `.gitkeep` 占位文件和 `target/` 构建产物，Tauri 源配置文件（`tauri.conf.json`、`Cargo.toml`、`src/main.rs`、`src/lib.rs`、`capabilities/*.json`）均不存在，`package.json` 无 Tauri CLI/API 依赖。按任务单规定标记为阻塞，未修改任何代码。建议后续起草 Tauri 工程初始化任务单。

## 背景

Sprint-03 Dashboard UI 已完成深色 SaaS 工作台外壳，但 `docs/sprint-03-summary.md` 和 `docs/26-desktop-dashboard-ui-redesign.md` 都记录了残余风险：Windows / Tauri 原生窗口顶部白色标题栏会破坏深色界面整体观感。

当前 `desktop-app/src-tauri/` 目录存在，但本地检查只确认到 `.gitkeep` 和 `target/` 构建产物；未确认是否有可提交的 Tauri 源配置文件。`target/**` 是构建输出，不能修改、不能提交。

本任务目标是先审计 Tauri 源配置现状，再在安全范围内完成深色标题栏最小修复；如果缺少必要 Tauri 源文件，则记录阻塞原因和后续方案，不得盲目重建 Tauri 工程。

## 用户目标

解决桌面端顶部白色系统标题栏与深色 UI 不一致的问题，让窗口顶部边框/标题栏尽量与整体深色主题一致。

Codex 保守拆解结论：

- 本任务只处理 Tauri 窗口标题栏 / 系统 chrome 的审计和最小修复。
- 不做 EXE 打包发布。
- 不改业务功能。
- 不改 Dashboard 页面布局。
- 不改后端、数据库、Provider、Auth、Credit、Payment。

## 本次只开发什么

- 审计 `desktop-app/src-tauri/` 目录，确认是否存在可提交的 Tauri 源配置文件，例如：
  - `tauri.conf.json` 或 `tauri.conf.json5`
  - `Cargo.toml`
  - `src/main.rs`
  - `src/lib.rs`
  - `capabilities/*.json`
- 如果 Tauri 源配置文件存在：
  - 采用 Tauri 2 官方支持的最小窗口配置，让窗口标题栏/系统 chrome 与深色 UI 尽量一致。
  - 优先选择不破坏窗口拖拽、关闭、最小化、最大化的方案。
  - 如需 frameless / decorations false / 自定义标题栏，必须同时实现可用的拖拽区域和窗口控制按钮，且不能影响现有页面布局。
- 如果 Tauri 源配置文件不存在或不可恢复：
  - 不得修改 `target/**`。
  - 不得重新初始化整个 Tauri 工程。
  - 将任务状态标记为 `BLOCKED_NEEDS_TAURI_SOURCE`。
  - 在 `PROGRESS.md` 和模块上下文中记录缺失文件、证据、建议的后续任务。
- 补充模块上下文：
  - 新增或更新 `docs/module-context/sprint-04-task-06-tauri-dark-titlebar/context.md`。
  - 记录 Tauri 源文件现状、最终采用方案、未采用方案、验证方式、残余风险和回滚方式。
- 完成后追加更新 `PROGRESS.md`。

## 本次不开发什么

- 不做 EXE packaging。
- 不生成安装包。
- 不新增自动更新能力。
- 不修改 Dashboard 布局、缩放算法、页面配色和业务卡片。
- 不修改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment。
- 不修改本地 OCR 服务。
- 不新增依赖，除非 Tauri 源配置已存在且缺少项目已声明必需的 Tauri 官方配置；如涉及依赖或 lockfile，必须先暂停请求用户确认。
- 不修改或提交 `desktop-app/src-tauri/target/**`。
- 不删除、移动或重命名大目录。

## 允许修改哪些文件

- `desktop-app/src-tauri/tauri.conf.json`（仅当文件已存在或项目明确需要补齐该源配置）
- `desktop-app/src-tauri/tauri.conf.json5`（仅当文件已存在或项目明确使用 JSON5 配置）
- `desktop-app/src-tauri/src/main.rs`（仅当文件已存在且需要最小窗口事件逻辑）
- `desktop-app/src-tauri/src/lib.rs`（仅当文件已存在且需要最小窗口事件逻辑）
- `desktop-app/src-tauri/capabilities/*.json`（仅当文件已存在且 Tauri 权限最小补齐必须修改）
- `desktop-app/src/App.vue`（仅当采用自定义标题栏且需要拖拽区域或窗口控制按钮）
- `desktop-app/src/components/dashboard/AppTopbar.vue`（仅当采用页面内标题栏整合方案）
- `desktop-app/src/styles/**`（仅当存在且需要标题栏样式；不存在则不要新建全局样式目录）
- `docs/module-context/sprint-04-task-06-tauri-dark-titlebar/context.md`（可新增）
- `PROGRESS.md`
- `tasks/current-task.md`（仅允许状态、分支、简短完成摘要、commit/PR 信息）

## 禁止修改哪些文件

- `desktop-app/src-tauri/target/**`
- `cloud-backend/**`
- `shared/**`
- `desktop-app/local-service/**`
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `package.json`
- `package-lock.json`
- `.github/**`
- 数据库文件、日志、构建产物、本地缓存和生成物
- 与标题栏无关的 Dashboard 页面业务逻辑

## 本地环境和服务规则

- 本任务不需要数据库、Redis、云后端、本地 OCR 服务或 Docker。
- 本地验证优先使用本机已安装 Node/npm 和 Rust/Tauri 环境。
- 不默认使用 Docker。
- 如果本机缺少 Rust/Tauri CLI，不要用 Docker 替代；先报告缺失环境，并用可运行的前端构建和静态配置检查作为替代验证。

## 注释语言要求

- CC 新增或修改代码注释时必须使用中文。
- 第三方协议、外部 API 固定术语、错误码、英文专有名词和工具原始输出除外。

## 是否允许新增依赖

默认不允许。

如果确实需要新增 Tauri 官方依赖、修改 `package.json`、`package-lock.json`、`Cargo.toml` 或 `Cargo.lock`，必须暂停并请求 Codex/用户更新任务单，不能直接修改。

## 是否涉及重大变更

是。

原因：Tauri 窗口标题栏、decorations、frameless、自定义窗口控制和 capabilities 都属于桌面壳行为变更，可能影响窗口拖拽、关闭、最小化、最大化、系统菜单和平台一致性。

本任务已明确允许在最小范围内审计和修复 Tauri 标题栏，但不得扩大到打包发布、权限扩张或依赖变更。

## 高风险边界

本任务允许触碰的高风险边界：

- Tauri 窗口配置
- Tauri 标题栏 / decorations / frameless 相关配置

本任务仍然禁止触碰：

- Tauri 权限扩张，除非现有 capabilities 缺失且必须最小补齐
- 数据库 schema / DDL / migration
- API / OpenAPI / shared DTO
- Auth / Token / 权限
- Provider / credit / payment / provider cost
- dependencies / lockfiles
- CI / workflows / deployment
- 删除文件、重命名目录、大规模重构

如果实现过程中发现必须触碰禁止边界，CC 必须暂停并请求 Codex/用户更新任务单。

## 验收标准

- [ ] 已审计 `desktop-app/src-tauri/`，明确哪些是源文件、哪些是 `target/**` 生成物。
- [ ] 没有修改或提交 `desktop-app/src-tauri/target/**`。
- [ ] 如果 Tauri 源配置存在，窗口标题栏/顶部系统 chrome 已采用最小深色方案。
- [ ] 如果采用 frameless 或自定义标题栏，窗口拖拽、关闭、最小化、最大化仍可用。
- [ ] 如果 Tauri 源配置不存在，任务明确标记为阻塞，并记录缺失文件和后续恢复方案。
- [ ] Vue 页面内顶部栏颜色仍与 `--bg-sidebar` / `--bg-app` 体系一致。
- [ ] 不破坏登录、Dashboard、OCR、历史、AI 文案、会员中心页面访问。
- [ ] 不修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment、依赖或 lockfile。
- [ ] 详细实现记录写入 `PROGRESS.md` 和模块上下文，不写入任务单正文顶部。

## 测试方式

必须运行：

```powershell
cd ad-assistant/desktop-app
npm run build
```

必须运行：

```powershell
git diff --check
```

如果 Tauri 源配置和本机 Tauri 环境可用，建议运行：

```powershell
cd ad-assistant/desktop-app
npm run tauri dev
```

如果 `npm run tauri dev` 不存在或环境不可用，CC 必须说明原因，并改用以下替代验证：

- 列出 `desktop-app/src-tauri/` 源文件审计结果。
- 说明没有修改 `target/**`。
- 说明采用或未采用的标题栏方案。
- 提供 `npm run build` 结果。

## 安全检查

- 不下发 API Key 到客户端。
- 不由客户端扣点。
- 不由客户端决定套餐。
- 不绕过云端授权。
- 不明文保存 Token。
- 不新增真实 AI Provider 调用。
- 不新增支付、充值到账或管理员赠送逻辑。
- 不扩张 Tauri 文件系统、shell、网络或远程执行权限。

## 回滚方案

- revert 本任务 commit 即可恢复 Tauri 标题栏配置和相关前端壳改动。
- 如果采用自定义标题栏，回滚对应 Vue/CSS 改动即可恢复旧窗口壳显示。
- 本任务不涉及数据库迁移和数据回滚。

## CC 必须暂停的情况

- 找不到可提交的 Tauri 源配置文件，且需要重新初始化 Tauri 工程。
- 需要修改 `desktop-app/src-tauri/target/**`。
- 需要新增依赖或修改 lockfile。
- 需要扩张 Tauri capabilities 权限。
- 需要改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment、CI。
- `npm run build` 失败且修复超出标题栏范围。
- 需要删除文件、重命名目录或做大规模重构。
- 发现 secrets、真实密钥、生产连接串或用户敏感数据泄露风险。
- 需要 Docker 但未获用户明确批准。

## 完成输出要求

执行者完成后必须用中文输出：

- 修改文件列表
- Tauri 源文件审计结果
- 实现内容
- 未实现内容
- 测试命令和结果
- 人工验证结果或未验证原因
- 自审结论
- reviewer-mode 自查结果
- 风险点
- 回滚方式
- 是否触发重大变更
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 是否只对 `tasks/current-task.md` 做了允许的状态类最小更新
- 中文 commit message
- PR title/body 中文摘要
- 合并后的中文交付说明，包括用户确认来源、PR 编号、合并方式和合并结果

## 任务单更新限制

- `tasks/current-task.md` 是执行规格，不是完成报告。
- CC 完成任务后只允许更新状态、分支、简短完成摘要、commit/PR 信息。
- 详细实现记录、测试结果、自审结论、reviewer-mode 结果和合并记录必须写入 `PROGRESS.md` 和对应模块上下文。
- 禁止把详细实现记录写到任务单正文顶部。
- 禁止修改 Codex/用户确认过的任务目标、范围、允许文件、禁止文件、验收标准、测试方式、安全要求和回滚方案。
