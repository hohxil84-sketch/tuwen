# 14 AI Agent 协作流程

## 角色

Claude Code / DeepSeek 是默认执行者，负责根据 Codex 编写或用户确认的任务单独立完成开发、测试、自审、任务分支提交和 PR 准备。

Codex 是任务单默认起草者和可选复核者；用户给出目标后，今后的任务单默认由 Codex 起草或更新，CC 只按确认后的任务单执行。

用户默认不参与日常细节，只确认任务方向、高风险变更和最终合并。

## 标准流程

1. 用户给出目标。
2. Codex 按 `CODEX.md` 的“Codex 从无到有起草任务单规则”根据用户目标起草或更新 `tasks/current-task.md`，补齐范围、禁区、验收标准、测试方式、依赖权限、高风险状态、环境规则和回滚方案。
3. CC 读取 `README.md`、`CLAUDE.md`、已确认的 `tasks/current-task.md`、相关 docs 和模块上下文。
4. CC 从 `main` 创建任务分支。
5. CC 输出简短计划、涉及文件、风险判断；高风险任务先等用户确认。
6. CC 实现当前任务。
7. CC 运行任务单要求的测试。
8. CC 完成自审清单，更新模块上下文和 `PROGRESS.md`。
9. CC 自审通过后，可以提交并 push 当前任务分支。
10. CC 创建 PR 或 draft PR，PR 内容包含范围、测试、自审结论和风险。
11. 用户确认 PR 可以合并后，CC 可以通过 GitHub PR 合并；用户、仓库管理员或明确授权的流程也可以合并 PR。

## 统一规则

- 一次只做一个任务，一个任务只对应一个 Git 分支。
- 用户只给目标时，Codex 负责把目标转成任务单。
- CC 不得自行扩大、重写或弱化 Codex/用户确认的任务单范围；如发现任务单缺失、冲突或不可执行，必须暂停并请求 Codex/用户更新。
- 只实现 `tasks/current-task.md` 明确允许的内容。
- CC 自审是默认门禁，Codex Review 是按需复核。
- 提交时只 stage 当前任务相关文件，不使用 `git add -A`。
- 每个完成的模块都要更新对应的 `docs/module-context/<module-or-task>/context.md`。
- 每个完成的模块或任务都要追加更新 `PROGRESS.md`，记录进度、自审、主要实现、测试、风险和回滚方式。
- `tasks/current-task.md` 是执行规格，不是完成报告；CC 完成任务后只允许更新状态、分支、简短完成摘要、commit/PR 信息，详细实现记录必须写入 `PROGRESS.md` 和模块上下文。
- CC 合并 PR 前必须有用户明确确认；合并后必须记录确认来源、合并方式和合并结果。
- 下一任务必须由 Codex 生成或更新新的任务单，并通过新的任务分支开始。
- 凡是需要安装到本机的依赖、SDK、CLI、运行时、模型、缓存、构建工具或其他外部工具，CC 默认必须优先安装或配置到 `D:` 盘；如果工具强制写入 `C:` 盘，必须先暂停说明原因、占用空间、风险和清理方式，等待用户确认。

## Bug 修复流程

1. 先复现或确认失败现象。
2. 找到根因并说明证据。
3. 制定解决方案，明确改哪些文件、风险和测试方式。
4. 按方案修改。
5. 跑相关测试和必要回归测试。
6. 反馈根因、修改、测试结果和残余风险。

根因不明确时，继续调查，不直接试改。

## 高风险边界

遇到以下边界，CC 必须先停下并等用户确认：

- 数据库 schema / DDL / migration
- API / OpenAPI / shared DTO
- Auth / Token / 权限
- Provider / credit / payment / provider cost
- Tauri permissions
- dependencies / lockfiles
- CI / workflows / deployment
- filesystem permissions
- remote command execution
- 删除文件、重命名目录、大规模重构

## 何时召回 Codex

- 用户明确要求 Review。
- CC 自审发现范围不确定。
- 高风险变更需要额外审查。
- 测试失败且无法在任务范围内修复。
- PR 前需要独立复核关键风险。
