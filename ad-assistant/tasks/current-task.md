# Current Task: Coding Standards Extensibility Guidelines

## Status

`IMPLEMENTED_SELF_REVIEW_PASSED`

## Background

第一期代码后续会持续增加功能和修改现有模块。当前编码规范强调安全和基本分层，但缺少明确的可扩展性、可修改性和后续演进规则。

## Goal

补充项目编码规范，要求新功能接入现有分层、避免硬编码未来变化点、集中维护契约和共享类型，并记录模块后续扩展入口。

## What To Build

- 在 `docs/15-coding-standards.md` 中新增“可扩展性与可修改性”章节。
- 明确前端、后端、Provider、计费、权限、API 契约等边界的扩展方式。
- 明确禁止无任务目标的大重构、重复手写前后端契约、把核心业务判断散落到 UI 或临时脚本。

## What Not To Build

- 不修改业务代码。
- 不新增工具、依赖、格式化配置或 CI。
- 不修改 API、数据库、Provider、Auth、Token、Credit、Tauri 或部署逻辑。

## Allowed Files

- `docs/15-coding-standards.md`
- `tasks/current-task.md`
- `PROGRESS.md`

## Forbidden Files

- 所有业务代码文件。
- 依赖文件、lockfile、CI、数据库迁移、OpenAPI、DTO。

## Acceptance Criteria

1. 编码规范包含可扩展性与可修改性规则。
2. 规则覆盖分层接入、集中配置/契约、局部化修改、模块上下文和回滚记录。
3. 没有业务代码改动。
4. `git diff --check` 通过。

## Test Method

- `git diff --check`

## Dependency Permission

不允许新增依赖。

## Major Change Status

No — 纯文档规范补充。

## Security Requirements

- 不加入 secrets、真实密钥、Token、生产连接串或用户隐私数据。
- 不放宽任何安全规则。

## Rollback Plan

revert 本次文档提交即可恢复旧版编码规范。

## Completion Output Required

- 修改文件
- 规则补充内容
- 自审结论
- 测试命令和结果
- PR 和合并结果
