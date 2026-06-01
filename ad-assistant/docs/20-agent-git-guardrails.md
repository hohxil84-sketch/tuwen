# 20 Agent Git 约束

## 适用场景

当需要判断能否提交、推送、建 PR，或需要确认当前任务的 Git 流程是否合规时，使用本规则。

## 进入提交前，必须确认

- 当前分支不是 `main`
- 只修改当前任务允许的文件
- 没有未确认的重大变更
- 测试已运行并记录结果
- Codex Review 已完成
- Codex Review 结论为 `允许提交`

## Review 范围

Codex Review 默认只看当前任务的 staged diff、任务单和必要模块上下文，不做全仓审查。

如果本次修改触及数据库、API、授权、Provider、点数、安全、CI 等高风险边界，才读取必要的相邻文件。

## 阻断条件

- 没有有效任务单
- 任务范围超出 allowed files
- 触碰 DDL、API、Provider、Auth/Token、credit、payment、Tauri、dependency、CI、security 等边界但没有用户确认
- 存在 secrets 或真实密钥
- Codex Review 返回阻断问题

## 执行规则

- 只 stage 本任务相关文件
- 不使用 `git add -A`
- 不在 `main` 上提交
- 不推 `main`
- 不 force push
- 不混合多个模块
- 不自行创建下一任务实现

## PR 规则

- base: `main`
- head: 当前任务分支
- PR 内容必须包含：任务范围、测试结果、Codex Review 结论、风险
- 只有 Codex 明确允许提交后，才允许建 PR 或合并
