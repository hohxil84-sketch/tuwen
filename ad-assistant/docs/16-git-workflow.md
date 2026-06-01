# 16 Git 工作流

## 基本原则

- 一任务一分支，一模块一分支。
- 当前分支不能是 `main`。
- 只提交当前任务相关文件。

## 提交前

1. 运行 `git status --short --branch`
2. 确认任务单有效
3. 确认没有未确认的重大变更
4. 确认测试结果已记录
5. 先做 Codex Review，再考虑提交

## 提交规则

- 不要用 `git add -A`
- 不要把无关文件混进同一个 commit
- Codex Review 未通过，不提交
- 提交目标只能是当前任务分支，推送命令只能是 `git push -u origin <current-branch>`
- 不要 `git push origin main`
- 不要 force push

## 合并规则

- `main` 只能通过 PR 合并
- PR base 为 `main`
- PR head 为当前任务分支
- PR 通过前必须有任务单、测试记录和 Codex Review 结论

## 相关规则

更详细的守卫规则见 `docs/20-agent-git-guardrails.md`。
