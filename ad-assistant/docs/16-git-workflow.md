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
