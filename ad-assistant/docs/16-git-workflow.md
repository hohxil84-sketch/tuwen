# 16 Git 工作流

## 分支规则

一个模块一个分支。
一个任务一个分支。

每次提交前必须由 Codex Review。
Codex Review 未通过，不允许提交。

建议命名：
- `codex/docs-bootstrap`
- `feature/auth-minimal`
- `feature/ocr-minimal`
- `feature/usage-stats`
- `feature/provider-log`

## 提交规则

提交必须小而清晰。

提交信息建议：

```text
type(scope): summary
```

类型：
- docs
- feat
- fix
- refactor
- test
- chore
- security

## 合并前检查

合并前必须确认：
- 当前任务单已完成
- 测试已执行
- 未越界开发
- 未触发未确认重大变更
- Codex Review 通过

## 提交前检查

提交前必须确认：
- 任务单有效
- 修改范围符合任务单
- 测试结果已记录
- 无未确认重大变更
- Codex Review 已完成
- Codex Review 明确允许提交

## 禁止

禁止：
- 一个分支混多个模块
- 无任务单提交业务代码
- 自动大规模格式化无关文件
- 删除用户未确认的文件
- 重写共享历史

详细 Agent Git 规则见 `docs/20-agent-git-guardrails.md`。
## Claude Code 提交位置规则

Claude Code / DeepSeek 不允许直接在 `main` 分支提交业务实现。

每次执行任务前必须先确认当前分支：

```powershell
git status --short --branch
```

如果当前分支是 `main`，必须先创建任务分支：

```powershell
git switch -c feature/<task-name>
```

分支命名规则：

- `feature/sprint-01-scaffold`：Sprint 或功能开发
- `fix/<scope>-<issue>`：缺陷修复
- `docs/<scope>`：纯文档修改
- `chore/<scope>`：工程配置或维护任务

提交位置：

- 本地提交只能提交到当前任务分支。
- 远端推送只能推送到 `origin/<current-branch>`。
- 禁止 `git push origin main`，除非用户明确要求并且 Codex Review 明确允许。
- 禁止 `git push --force` 或重写共享历史。

标准提交流程：

```powershell
git status --short --branch
git add <only-task-related-files>
git commit -m "type(scope): summary"
git push -u origin <current-branch>
```

合并规则：

- `main` 是稳定主干，只能通过 PR 合并。
- PR base 必须是 `main`。
- PR head 必须是任务分支。
- Codex Review 未通过时，不允许提交到 `main`，不允许合并 PR。
