# Claude Code + DeepSeek 执行规则

Claude Code + DeepSeek 只负责按任务单实现当前任务，不负责自行开新任务或扩范围。

## 必须先读

1. `README.md`
2. `CODEX.md`
3. `CLAUDE.md`
4. `tasks/current-task.md`
5. 相关 `docs/*.md`
6. 如果任务涉及已有模块的扩展或修改，读取对应的 `docs/module-context/<module-or-task>/context.md`

## 执行边界

- 只实现 `tasks/current-task.md` 明确允许的内容。
- 没有任务单，不写业务代码。
- 没有用户确认的重大变更，不碰数据库 schema、API contract、Provider、Auth/Token、credit/payment、Tauri、依赖、CI、filesystem permissions 或 remote execution 等边界。
- 遇到需要修改允许范围外的文件，立即停止并报告。

## 工作方式

- 一次只做一个任务，一个任务只用一个分支。
- 完整实现当前任务后再交给 Codex Review，不要把同一任务拆成多轮小交付。
- 运行任务单要求的测试并记录结果。
- 更新 `tasks/current-task.md` 和对应模块上下文。

## Git 规则

- 开始前先运行 `git status --short --branch`。
- 如果当前分支是 `main`，先切到任务分支再继续。
- 只 stage 当前任务相关文件，不使用 `git add -A`。
- Codex Review 未通过时，不提交、不 push、不 self-merge。
- 只推送当前任务分支，不推 `main`，不 force push。
- 合并只能通过 PR，base 为 `main`，head 为当前任务分支。

## 输出要求

完成任务后只输出：

- 修改文件
- 实现内容
- 未实现内容
- 测试命令和结果
- 风险
- 是否触发重大变更
- 是否更新模块上下文
- 等待 Codex Review
