# Codex 工作规则

Codex 在本项目中不再作为默认强制门禁，也不默认负责任务单起草。CC/DeepSeek 默认根据用户目标起草任务单并独立执行。Codex 只在用户明确召回、CC 请求专项复核、或任务触及高风险边界时参与任务拆分、Review、安全/API/数据库/Provider/成本/发布风险判断。

## 工作边界

- 默认不主动继续项目任务。
- 只围绕用户明确指定的任务、commit、PR、diff 或问题开展工作。
- 默认只审查本次修改的文件、当前 diff、任务单和相关模块上下文。
- 不做全仓审查；只有当修改触及数据库、API、授权、Provider、点数、安全、CI、Tauri、依赖等高风险边界时，才读取必要的相邻文件。
- 未经用户确认，不执行会改变外部状态的 Git、Docker、数据库、CI、提交、推送或 PR 操作。

## CC 自主开发原则

- CC/DeepSeek 默认独立开发、测试、自审、提交到任务分支和准备 PR。
- CC/DeepSeek 默认负责起草或更新 `tasks/current-task.md`。
- Codex Review 是可选复核，不是每次提交的强制条件。
- Codex 被召回时，只给出结论、风险和必要下一步，不扩展到无关范围。
- 如果 Codex 发现任务越界、高风险未确认、测试证据不足或 Git 流程不合规，直接指出并建议暂停。

## 高风险边界

以下边界必须由 CC 先暂停并获得用户确认；Codex 被召回时重点复核这些边界：

| 边界 | 说明 |
|------|------|
| 数据库 schema / DDL / migration | 列类型、约束、索引、迁移脚本 |
| API contract / OpenAPI / shared DTO | 请求/响应结构、错误码、状态码语义 |
| Provider 接口 | Provider 基类、路由、模型选择、真实 Provider 调用 |
| Auth / Token | JWT 结构、刷新逻辑、权限模型、设备绑定 |
| Credit / Payment | 扣费逻辑、额度计算、定价、账本 |
| Tauri 权限 | 文件系统、网络、sidecar 声明 |
| 依赖变更 | `pyproject.toml`、`package.json`、lockfiles |
| 本地 Python 服务启动方式 | sidecar 配置、CLI 调用路径、进程管理 |
| CI / 部署 | workflow、Dockerfile、环境变量约定 |
| 文件/目录破坏性变更 | 删除文件、重命名目录、大规模重构 |

## Review 规则

Codex Review 输出按以下顺序：

1. 阻断问题
2. 风险问题
3. 测试和证据
4. 验收结论
5. 下一步建议

结论使用：

- `复核通过`：未发现阻断问题，剩余风险可接受。
- `需要修复`：存在阻断问题或证据不足。
- `需要用户确认`：触碰高风险边界或范围不明确。

## Git 建议

- CC 可以在任务分支自审通过后提交和 push。
- CC 不直接 push `main`，不 force push；未经用户明确确认，不 self-merge。
- 用户明确确认某个 PR 可以合并后，CC 可以通过 GitHub PR 合并，并记录确认来源和合并结果。
- PR base 必须是 `main`，head 必须是当前任务分支。
- 高风险任务、失败测试、范围不确定或用户要求时，建议 PR 前召回 Codex 复核。

## 模块上下文

- 每个完成的模块都要更新 `docs/module-context/<module-or-task>/context.md`。
- 新任务开始前由 CC 读取、起草或更新当前任务单和对应模块上下文。
- Codex 被召回维护上下文时，只记录已验证事实、测试结果、风险和后续注意事项。

## 交流规则

- 需要给 Claude Code / DeepSeek 的下一步说明时，用中文，简短明确。
- 需要向用户汇报时，直接说明结论、风险和下一步，不扩展到无关范围。
