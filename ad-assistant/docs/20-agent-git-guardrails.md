# 20 Agent Git 管理规则

## 最高规则

每次提交前必须经过 Codex Review。

没有 Codex Review 结论，不允许提交。
Codex Review 未通过，不允许提交。
发现未确认重大变更，不允许提交。

## 分支规则

一个任务一个分支。
一个模块一个分支。

分支命名：
- `docs/*`
- `feature/*`
- `fix/*`
- `security/*`
- `review/*`

示例：
- `feature/sprint-01-auth-minimal`
- `feature/sprint-01-ocr-minimal`
- `security/token-storage-review`
- `docs/provider-cost-rules`

禁止：
- 一个分支混多个模块
- 在主分支直接开发
- 在无任务单的分支写业务代码
- 用一个提交混合无关功能

## 提交前闸门

提交前必须满足：
1. 有有效任务单。
2. 修改范围符合任务单。
3. 测试已执行并记录结果。
4. 无未确认重大变更。
5. Codex Review 已完成。
6. Codex Review 结论为通过。

## 提交信息

提交信息格式：

```text
type(scope): summary
```

允许 type：
- `docs`
- `feat`
- `fix`
- `test`
- `chore`
- `security`
- `review`

示例：

```text
docs(guardrails): add agent git review gate
feat(auth): add minimal login endpoint
security(token): harden refresh token storage
```

## Agent 修改限制

Claude Code + DeepSeek：
- 只能在任务单允许范围内修改文件。
- 禁止修改重大变更项，除非任务单明确授权且用户已确认。
- 禁止自动格式化无关文件。
- 禁止提交代码。
- 完成后只输出修改、测试、风险，等待 Codex Review。

Codex：
- 默认先 Review。
- 需要改代码或文档时，必须说明原因和范围。
- 不得绕过任务单直接开发未来功能。
- Review 通过后，才允许执行提交或授权提交。

## 重大变更保护

以下文件或目录修改必须先确认：
- `shared/**`
- `shared/openapi/**`
- `shared/dto/**`
- `cloud-backend/app/providers/**`
- `cloud-backend/migrations/**`
- `cloud-backend/app/models/**`
- `cloud-backend/app/services/auth*/**`
- `cloud-backend/app/services/credit*/**`
- `desktop-app/src-tauri/**`
- 自动更新配置
- Token/Auth 相关代码
- 支付/扣费相关代码
- Provider 接口定义

如果任务需要修改以上范围，必须先输出：
1. 修改原因
2. 风险点
3. 影响范围
4. 回滚方案
5. 是否兼容旧版本
6. 是否需要数据库迁移

用户确认前禁止执行。

## PR 规则

每个 PR 必须包含：
- 任务单链接或内容
- 修改范围
- 测试结果
- 是否涉及重大变更
- 回滚方式
- 安全影响
- Codex Review 结论

## 合并前检查

合并前必须通过：
- 任务单验收
- 自动化测试或手工测试记录
- Codex Review
- 无未确认重大变更
- 无 API Key、Token、密码泄露
- 无前端直连第三方 AI API
- 无客户端扣点或客户端决定套餐

## 禁止提交清单

禁止提交：
- 未经 Review 的代码
- 未经确认的数据库迁移
- 未经确认的 API 契约变更
- 未经确认的 Provider 接口变更
- 未经确认的 Tauri 权限变更
- 未经确认的 Token 机制变更
- 包含真实密钥、Token、密码的文件
- 与任务单无关的大规模格式化
- BACKLOG、FUTURE、BLOCKED 功能实现
## Branch And Push Guardrails For Agents

Claude Code / DeepSeek must treat `main` as a protected stable branch.

Before writing or committing, the agent must run:

```powershell
git status --short --branch
```

If the current branch is `main`, the agent must create or switch to a task branch before continuing:

```powershell
git switch -c feature/<task-name>
```

Required branch targets:

- Development work: `feature/<task-name>`
- Bug fixes: `fix/<scope>-<issue>`
- Documentation only: `docs/<scope>`
- Tooling/config maintenance: `chore/<scope>`

Commit rules:

- Stage only files that belong to the current task.
- Do not use `git add -A` when unrelated or unreviewed files exist.
- Do not commit on `main`.
- Do not commit if Codex Review reports blocking issues.
- Do not commit if the task changes database schema, API contracts, Provider interfaces, Token logic, Tauri permissions, or payment logic without explicit user confirmation.

Push rules:

- Push only the current task branch:

```powershell
git push -u origin <current-branch>
```

- Do not run `git push origin main`.
- Do not force push.
- Do not rewrite shared history.

Pull request rules:

- PR base: `main`.
- PR head: current task branch.
- PR title format: `[task] short summary`.
- PR body must include scope, tests, Codex Review result, and known risks.
- Merge is allowed only after Codex Review explicitly says `允许提交` or `允许合并`.
