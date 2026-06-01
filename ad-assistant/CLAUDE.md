# Claude Code + DeepSeek 执行规则

Claude Code + DeepSeek 是本项目的一线开发与自审执行者。默认根据用户目标独立起草任务单，并完成开发、测试、自审、提交到任务分支和准备 PR；只有触碰高风险边界、范围不清、测试失败无法自行解决，或用户明确要求时，才暂停并请求用户或 Codex 介入。

## 必须先读

1. `README.md`
2. `CLAUDE.md`
3. `tasks/current-task.md`（如果没有有效任务单，先由 CC 起草或更新）
4. 相关 `docs/*.md`
5. 如果任务涉及已有模块的扩展或修改，读取对应的 `docs/module-context/<module-or-task>/context.md`
6. 需要 Codex 专项复核时，再读取 `CODEX.md`

## 执行边界

- 只实现 `tasks/current-task.md` 明确允许的内容。
- 没有有效任务单时，先根据用户目标起草或更新 `tasks/current-task.md`，再写业务代码。
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

## 工作方式

- 一次只做一个任务，一个任务只用一个分支。
- 用户只给目标时，CC 先把目标转成完整任务单。
- 从 `main` 创建任务分支后再开发。
- 完整实现当前任务，不把同一任务拆成多轮小交付。
- 运行任务单要求的测试并记录结果。
- 更新 `tasks/current-task.md` 和对应模块上下文。
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

## 任务单生成规则

CC 负责维护 `tasks/current-task.md`。每个任务单必须包含：

- 任务目标和背景
- What To Build
- What Not To Build
- Allowed Files
- Forbidden Files
- Acceptance Criteria
- Test Method
- Dependency Permission
- Major Change Status
- Security Requirements
- Rollback Plan
- Completion Output Required

如果用户目标不完整，CC 应先做保守拆解；只有目标无法判断、会触碰高风险边界或存在互斥选择时，才暂停询问用户。

## 自审清单

完成任务前，必须自审并在交付说明中明确结论：

- 是否只实现了 `tasks/current-task.md`
- 是否任务单由 CC 起草或更新且字段完整
- 是否只修改了 allowed files 或已说明必要例外
- 是否没有混入无关文件
- 是否没有新增未授权依赖
- 是否没有触碰未确认的高风险边界
- 是否没有 secrets、真实密钥、Token 或生产连接串
- 是否完成任务单要求的测试
- 是否更新模块上下文
- 是否追加更新 `PROGRESS.md`
- 是否列出未实现内容和残余风险

## Git 规则

- 开始前先运行 `git status --short --branch`。
- 如果当前分支是 `main`，先切到任务分支再继续。
- 只 stage 当前任务相关文件，不使用 `git add -A`。
- 自审通过后，可以提交到当前任务分支并 push 当前任务分支。
- 不直接 push `main`，不 force push。
- 可以创建 PR 或 draft PR，但不能 self-merge。
- 合并只能通过 PR，base 为 `main`，head 为当前任务分支。
- 高风险任务、测试异常、范围不确定或用户要求时，提交/PR 前先请求 Codex 或用户复核。

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
