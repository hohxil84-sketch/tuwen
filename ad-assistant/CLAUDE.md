# Claude Code + DeepSeek 执行规则

Claude Code + DeepSeek 是本项目的一线开发与自审执行者。默认根据 Codex 编写或用户确认的任务单完成开发、测试、自审、提交到任务分支和准备 PR；只有触碰高风险边界、范围不清、测试失败无法自行解决，或用户明确要求时，才暂停并请求用户或 Codex 介入。

## 必须先读

1. `README.md`
2. `CLAUDE.md`
3. `tasks/current-task.md`（今后任务单默认由 Codex 起草或更新；没有有效任务单时，CC 必须暂停并请求 Codex/用户补齐）
4. 相关 `docs/*.md`
5. 如果任务涉及已有模块的扩展或修改，读取对应的 `docs/module-context/<module-or-task>/context.md`
6. 需要 Codex 专项复核时，再读取 `CODEX.md`

## 执行边界

- 只实现 `tasks/current-task.md` 明确允许的内容。
- 没有有效任务单时，先暂停并请求 Codex/用户起草或更新 `tasks/current-task.md`，再写业务代码。
- CC 不得自行扩大、重写或弱化 Codex/用户确认的任务单范围；如发现任务单缺失、冲突或不可执行，必须先反馈并等待更新。
- 不自行开发 BACKLOG、FUTURE、BLOCKED 或任务单未写明的功能。
- 遇到需要修改 allowed files 之外的文件，先判断是否属于任务必要范围；如果会扩大任务目标，立即停止并报告。
- 不保存真实 API Key、Token、密码、生产数据库连接串或用户隐私数据。

## 高风险暂停规则

以下边界必须先停止，输出方案、风险、影响范围、测试方式和回滚方式，等待用户确认：

- 数据库 schema / DDL / migration
- API contract / OpenAPI / shared DTO
- Auth / Token / 权限模型
- Credit / Payment / 扣费 / provider cost
- Provider 接口、模型路由或真实 AI Provider 调用
- Tauri 权限、本地服务启动、文件系统权限、remote execution
- CI / deployment / Dockerfile / 环境变量约定
- 新增依赖、升级核心依赖、修改 lockfile
- 删除文件、重命名目录、大规模重构

## 本地安装位置规则

- 凡是需要安装到本机的桌面级应用，默认必须安装到 `D:\APPLICATION`。
- 凡是需要安装到本机的环境依赖、SDK、CLI、运行时、模型、缓存、构建工具或其他外部工具，默认必须安装或配置到 `D:\locaPath`。
- 不得默认把新工具、桌面应用、依赖缓存、模型缓存或大体积构建缓存安装到 `C:` 盘。
- 如果某个安装器、系统组件或工具链强制写入 `C:` 盘，CC 必须先暂停，说明原因、预计占用空间、可选安装位置、风险、清理方式和回滚方式，等待用户确认。
- 任务单涉及安装或依赖下载时，CC 必须在计划和交付说明中写明实际安装位置、缓存位置和是否触碰 `C:` 盘。
- 项目已有依赖解析不受此规则阻止，但新增依赖、系统工具、模型和大缓存必须按本规则执行。

## 工作方式

- 一次只做一个任务，一个任务只用一个分支。
- 用户只给目标时，先由 Codex 把目标转成完整任务单；CC 只根据已确认任务单执行。
- 从 `main` 创建任务分支后再开发。
- 完整实现当前任务，不把同一任务拆成多轮小交付。
- 运行任务单要求的测试并记录结果。
- 任务完成后只允许对 `tasks/current-task.md` 做状态类最小更新；详细实现记录必须写入 `PROGRESS.md` 和对应模块上下文。
- 每完成一个模块或任务，必须追加更新 `PROGRESS.md`，记录进度、自审结论、主要实现、测试结果、风险和回滚方式。
- 如果测试失败，先自行定位和修复；无法在当前任务范围内修复时，停止并报告。

## Bug 修复规则

遇到 bug 或失败测试时，CC 不允许直接试改。必须按以下顺序处理：

1. 复现问题或确认失败现象。
2. 定位根因，说明问题来自代码、配置、数据、环境还是测试。
3. 制定解决方案，列出计划修改的文件和风险。
4. 按方案完成修改。
5. 运行相关测试和必要回归测试。
6. 反馈根因、修改内容、测试结果、残余风险和是否需要后续任务。

如果根因不明确，先继续调查；不能用猜测性修改替代根因分析。

## 任务单执行规则

任务单默认由 Codex 按 `CODEX.md` 的“Codex 从无到有起草任务单规则”起草或更新。

CC 负责读取并执行 `tasks/current-task.md`，不得在未经 Codex/用户确认的情况下自行改写任务目标、Allowed Files、Forbidden Files、Acceptance Criteria、Test Method、Security Requirements 或 Rollback Plan。

如果任务单缺字段、范围冲突、不可执行，或需要修改 allowed files 之外的文件，CC 必须暂停并请求 Codex/用户更新任务单，不能自行补齐后继续开发。

任务单是执行规格，不是完成报告。CC 完成任务后，`tasks/current-task.md` 只允许更新：

- 状态
- 分支
- 简短完成摘要
- commit / PR 信息

CC 不得把详细实现记录、测试输出、自审全文、reviewer-mode 全文或合并记录写入任务单正文顶部。详细完成记录必须写入 `PROGRESS.md` 和 `docs/module-context/<module-or-task>/context.md`。CC 不得修改 Codex/用户确认过的任务目标、范围、允许文件、禁止文件、验收标准、测试方式、安全要求和回滚方案。

## Reviewer-mode 自查

CC 自审不是最终质量门禁。完成实现和常规自审后，CC 必须立刻切换到 reviewer-mode，对自己的改动做一次独立审查；审查时停止继续写功能代码，按代码审查标准优先寻找 bug、行为回归、安全/隐私风险、测试缺口、范围越界和未处理的高风险边界。

Reviewer-mode 输出必须 findings first，按严重程度排序；没有发现问题时，也必须明确写出“未发现阻塞问题”和剩余风险/测试缺口。若 reviewer-mode 发现阻塞或高风险问题，本次自审视为未通过，必须先修复、补充必要测试、重新运行相关测试，并再次执行 reviewer-mode。

高风险任务必须在 reviewer-mode 通过后再请求 Codex 复核；包括但不限于数据库 schema/DDL/migration、API contract/OpenAPI/shared DTO、Provider/模型路由/真实 AI 调用、Auth/Token/权限、Credit/Payment/扣费/provider cost、Tauri 权限、本地服务启动、文件系统权限、CI/依赖/环境变量、删除/清空/清理用户数据或沙箱文件。

Reviewer-mode 交付说明必须包含：实际审查范围、发现的问题和修复结果、未修复风险、测试缺口、实际运行的测试命令和结果、`git status --short --branch`、`git diff --cached --name-status`。

## 自审清单

完成任务前，必须自审并在交付说明中明确结论：

- 是否只实现了 `tasks/current-task.md`
- 是否任务单由 Codex 起草或更新，或已由用户明确确认，且字段完整
- 是否只修改了 allowed files 或已说明必要例外
- 是否没有混入无关文件
- 是否没有新增未授权依赖
- 是否没有触碰未确认的高风险边界
- 是否没有 secrets、真实密钥、Token 或生产连接串
- 是否完成任务单要求的测试
- 是否完成 reviewer-mode 自查，且阻塞/高风险发现已修复
- 是否更新模块上下文
- 是否追加更新 `PROGRESS.md`
- 是否只对 `tasks/current-task.md` 做了允许的状态类最小更新
- 是否列出未实现内容和残余风险

## Git 规则

- 开始前先运行 `git status --short --branch`。
- 开始任务、提交前和推送前都必须运行 `git fetch origin --prune`；如果网络、认证或权限导致 fetch 失败，立即停止并报告，不得使用缓存的远端引用继续。
- 新任务分支必须基于最新 `origin/main` 创建，例如 `git switch -c <task-branch> origin/main`；不得默认本地 `main` 已同步。
- 如果当前分支是 `main`，先基于 `origin/main` 创建或切到任务分支再继续。
- 当前分支已有 upstream 时，提交前和推送前运行 `git rev-list --left-right --count "HEAD...@{upstream}"`；右侧计数大于 0 时，必须先确定 rebase 或 merge 方案，不得直接提交或推送。
- 当前分支没有 upstream 时，必须确认远端不存在同名分支，或先建立并检查正确的 upstream。
- 不得在存在未提交改动时盲目执行 `git pull`；同步前先保护并检查本地改动，明确选择 rebase 或 merge，禁止默认 pull 产生意外合并提交。
- 只 stage 当前任务相关文件，不使用 `git add -A`。
- 在存在任何 unrelated dirty files 时，提交前必须先运行并展示 `git status --short --branch` 和 `git diff --cached --name-status`。
- 用户或 Codex 明确确认 staged 文件列表前，不得 `git commit`。
- 如果 staged 文件中出现任务单 allowed files 之外的文件，必须停止并取消 stage；不得用“顺手修复”“本地生成”“构建需要”作为混入理由。
- 如果需要修改 forbidden files 或高风险边界文件，必须先更新任务单并等待用户确认，不能在当前任务 commit 中夹带。
- 自审、reviewer-mode 自查和远端同步门禁均通过后，可以提交到当前任务分支并 push 当前任务分支。
- 不直接 push `main`，不 force push。
- 可以创建 PR 或 draft PR；未经用户明确确认，不能 self-merge。
- 用户明确确认某个 PR 可以合并后，CC 可以通过 GitHub PR 合并该 PR，并在交付说明中记录确认来源和合并结果。
- 合并只能通过 PR，base 为 `main`，head 为当前任务分支。
- 高风险任务、测试异常、范围不确定或用户要求时，提交/PR 前先请求 Codex 或用户复核；CC 自审和 reviewer-mode 自查不能替代 Codex 高风险复核。

## Git 与交付说明语言

- CC 提交、推送、创建 PR、更新 PR、合并 PR 和最终交付说明时，面向用户和项目记录的文字必须使用中文。
- 必须使用中文说明的内容包括：commit message、PR title、PR body、自审结论、reviewer-mode 结果、测试结果、风险说明、回滚说明、用户确认来源、合并方式和合并结果。
- `git commit` 前必须先写清楚中文提交说明；禁止使用空泛说明，例如 `update`、`fix`、`changes`、`misc`、`wip`。
- PR 创建或更新时必须写中文正文，至少包含任务范围、修改摘要、测试结果、风险、回滚方式和是否需要用户确认。
- 合并 PR 后必须用中文报告 PR 编号、用户确认来源、合并方式、合并结果和后续注意事项。
- 允许保留英文的内容仅限命令、路径、文件名、分支名、commit hash、PR 编号、错误码、API 名称、第三方协议术语和工具原始输出。

## 输出要求

完成任务后输出：

- 修改文件
- 实现内容
- 未实现内容
- 自审结论
- 测试命令和结果
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- Git 状态、commit/PR 信息（如果已创建）
