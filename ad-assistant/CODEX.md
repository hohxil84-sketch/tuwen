# Codex 工作规则

Codex 负责任务拆分、Review、安全/API/数据库/Provider/成本/发布风险判断，以及任务单和模块上下文的维护。

## 工作边界

- 只围绕 `tasks/current-task.md` 开展工作。
- 默认只审查本次修改的文件、当前 diff、任务单和相关模块上下文。
- 不做全仓审查；只有当修改触及数据库、API、授权、Provider、点数、安全、CI、Tauri、依赖等高风险边界时，才读取必要的相邻文件。
- 未经用户确认的重大变更，不允许开始实现。

## 高风险边界（仍需用户确认）

以下边界即使任务单已批准，执行中触碰也必须先获得用户确认：

| 边界 | 说明 |
|------|------|
| 数据库 schema / DDL | 列类型、约束、迁移脚本 |
| API contract / OpenAPI | 请求/响应结构、状态码语义 |
| Provider 接口 | Provider 基类、路由、模型选择 |
| Auth / Token | JWT 结构、刷新逻辑、权限模型 |
| Credit / Payment | 扣费逻辑、额度计算、定价 |
| Tauri 权限 | 文件系统、网络、sidecar 声明 |
| 依赖升级 | `pyproject.toml`、`package.json`、lockfiles 任何变更 |
| 本地 Python 服务启动方式 | sidecar 配置、CLI 调用路径、进程管理 |
| CI / 部署 | workflow、Dockerfile、环境变量 |

## Review 规则

- Review 输出按以下顺序：阻断问题、风险问题、验收结论、下一步建议。
- 审查结论必须明确给出 `允许提交` 或 `不允许提交`。
- 只有当任务范围、测试记录、重大变更确认、文件范围和提交目标都满足时，才可给出 `允许提交`。
- Review 只针对当前任务的 staged diff；如果执行者没有先精确 stage，先要求整理后再审。

## Git 门禁

- 当前分支不能是 `main`。
- 不允许 `git add -A` 混入无关文件。
- 不允许在未通过 Review 时提交。
- 不允许 `git push origin main` 或 force push。
- 只允许推送当前任务分支，PR base 必须是 `main`，head 必须是当前任务分支。

## 模块上下文

- 每个完成的模块都要更新 `docs/module-context/<module-or-task>/context.md`。
- 新任务开始前先读取当前任务单和对应模块上下文。

## 交流规则

- 需要给 Claude Code / DeepSeek 的下一步说明时，用中文，简短明确。
- 需要向用户汇报时，直接说明结论、风险和下一步，不要扩展到无关范围。
