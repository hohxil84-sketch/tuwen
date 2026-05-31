# Claude Code + DeepSeek 执行规则

Claude Code + DeepSeek 在本项目中只负责按任务单执行开发。

## 绝对规则

没有任务单，不允许写代码。

只允许开发 `tasks/current-task.md` 中明确写出的内容。

每次提交前必须由 Codex Review。
Claude Code + DeepSeek 不允许自行提交。

禁止自行开发未来功能。
禁止扩大范围。
禁止大规模重构。
禁止自动升级核心依赖。

## 每次开发前必须读取

1. `README.md`
2. `CODEX.md`
3. `CLAUDE.md`
4. `tasks/current-task.md`
5. 与任务相关的 `docs/*.md`
6. 如果任务涉及已有模块的扩展或修改，必须读取对应的 `docs/module-context/<module-or-task>/context.md`

## 必须遵守的任务边界

每个任务单必须明确：
- 本次只开发什么
- 本次不开发什么
- 允许修改哪些文件
- 禁止修改哪些文件
- 验收标准
- 测试方式
- 是否允许新增依赖
- 是否涉及重大变更

任务单没有写的，一律不做。

## 函数注释规则

Claude Code / DeepSeek 写代码时，每新增一个函数，必须添加简短中文注释，说明该函数的作用即可，不需要写过长说明。

## 禁止行为

禁止：
- API Key 放客户端
- 前端直接调用 OpenAI、DeepSeek、Claude、ComfyUI 等第三方 API
- 客户端直接扣点
- 客户端决定套餐
- 绕过云端授权
- 本地保存明文 Token
- 未授权调用高级 AI
- 自动修改数据库结构
- 自动修改 API 契约
- 自动修改 Provider 接口
- 自动修改 Tauri 权限
- 自动修改本地 Python 服务启动方式
- 删除文件
- 重命名目录
- 引入远程命令执行能力

## 遇到重大变更

如果任务执行过程中必须触发重大变更，立即停止开发，并输出：
1. 修改原因
2. 风险点
3. 影响范围
4. 回滚方案
5. 是否兼容旧版本
6. 是否需要数据库迁移

等待用户确认后才能继续。

## 完成输出

每次完成任务后必须输出：
- 修改文件列表
- 实现内容
- 未实现内容
- 测试命令和结果
- 风险点
- 是否触发重大变更
- 是否已更新对应 `docs/module-context/<module-or-task>/context.md`
- 等待 Codex Review，不得自行提交

## 模块完成后的交接规则

每个模块完成后，Claude Code / DeepSeek 只允许等待 Codex Review。

Review 通过并合并到 `main` 后：
- 不得在原分支继续开发下一个模块。
- 不得自行创建下一个模块的业务实现。
- 必须等待 Codex 准备下一任务文档。
- 必须等待 Codex 保存或更新模块上下文：`docs/module-context/<module-or-task>/context.md`。
- 必须等待用户开启新会话并切换到新的任务分支。

新模块开发必须使用新的任务分支和新的任务文档。

## 模块上下文规则

后续扩展或修改某个已完成模块时，Claude Code / DeepSeek 必须先读取该模块上下文文件，再开始实现。

每次修改模块后，执行者必须把新增事实交给 Codex Review，由 Codex 确认并维护上下文文件。上下文必须记录：
- 本次修改目标
- commit 或 PR
- 改动文件
- 测试结果
- 已知风险
- 后续修改注意事项

## Git 提交规则

Claude Code / DeepSeek 必须遵守以下 Git 规则：

1. 开发前先执行 `git status --short --branch`。
2. 如果当前在 `main`，必须先切任务分支，例如 `git switch -c feature/sprint-01-scaffold`。
3. 不允许在 `main` 上提交业务代码。
4. 只允许提交当前任务相关文件，不允许把无关文件混入同一个 commit。
5. Codex Review 未通过时，不允许提交。
6. 提交后只能推送当前任务分支：`git push -u origin <current-branch>`。
7. 不允许 `git push origin main`。
8. 不允许 `git push --force`。
9. 合并到 `main` 必须通过 PR，PR base 为 `main`，PR head 为当前任务分支。

推荐提交消息格式：

```text
type(scope): summary
```

示例：

```text
docs(git): clarify branch and push rules
feat(scaffold): add sprint 01 project skeleton
fix(auth): correct device binding validation
```

## Context And Review Scope Rules

为减少 token 消耗，Claude Code / DeepSeek 默认遵守以下上下文边界：

- 一个模块完成后，必须向 Codex 提供当前模块总结、README 更新内容、开发记录和测试结果。
- 一个模块对应一个新会话；新会话只读取当前模块相关文件。
- 默认不做全项目分析；只有任务单、模块上下文或用户明确要求时，才扩大读取范围。
- 默认少开自动审查和自动修复；只有用户明确要求，或修改触及数据库、API、授权、Provider、点数、安全、CI 等高风险边界时，才做必要的专项审查。
- 用户要求 Codex `Review` 时，执行者必须只提供本次修改文件、当前 diff、任务单和相关模块上下文，不要求 Codex 审查整个仓库。
- 如本次修改文件暴露跨模块风险，执行者必须明确说明风险链路，方便 Codex 只读取必要的相邻文件。
