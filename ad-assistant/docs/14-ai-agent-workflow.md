# 14 AI Agent 协作流程

## 角色

Codex 负责定规则、拆任务、Review、风险判断和提交门禁。

Claude Code / DeepSeek 负责按任务单实现当前任务。

## 统一规则

1. 一次只做一个任务，一个任务只对应一个 Git 分支。
2. 只实现 `tasks/current-task.md` 明确允许的内容。
3. 没有用户确认的重大变更，不开始实现。
4. 同一任务由 Claude Code / DeepSeek 一次性完成，再交给 Codex Review。
5. Codex Review 默认只看当前任务的 staged diff、任务单和必要上下文，不做全仓审查。
6. 只有 Codex 明确 `允许提交` 后，才可以 commit、push 或建 PR。
7. 提交时只 stage 当前任务相关文件，不使用 `git add -A`。
8. 每个完成的模块都要更新对应的 `docs/module-context/<module-or-task>/context.md`。
9. 下一任务必须通过新的任务单和新的任务分支开始。

## 高风险边界

遇到以下边界，必须先停下并等用户确认：

- 数据库 schema
- API / OpenAPI / shared DTO
- Auth / Token
- Provider / credit / payment
- Tauri permissions
- dependencies
- CI / workflows
- filesystem permissions
- remote command execution
