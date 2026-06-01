# 20 Agent Git 约束

## 适用场景

当需要判断能否提交、推送、建 PR，或确认当前任务的 Git 流程是否合规时，使用本规则。

## 默认门禁

CC 自审是默认提交门禁。Codex Review 是按需复核，不再是每次提交的强制条件。

进入提交前，CC 必须确认：

- 当前开发分支不是 `main`
- 当前任务单有效；没有有效任务单时，CC 已先起草或更新 `tasks/current-task.md`
- 只修改当前任务相关文件
- 没有混入无关文件
- 没有未确认的高风险变更
- 没有 secrets、真实密钥、Token 或生产连接串
- 测试已运行并记录结果
- 模块上下文已更新
- `PROGRESS.md` 已追加更新
- 自审清单已完成

## 必须暂停的情况

- 没有有效任务单，且 CC 没有先根据用户目标补齐 `tasks/current-task.md`
- 任务范围超出 allowed files 且无法证明必要性
- 触碰 DDL、API、Provider、Auth/Token、credit、payment、Tauri、dependency、CI、security 等边界但没有用户确认
- 存在 secrets 或真实密钥
- 测试失败且无法在当前任务范围内修复
- bug 根因不明确却准备直接改代码
- 当前分支是 `main`
- 需要删除文件、重命名目录或做大规模重构

## 执行规则

- 只 stage 本任务相关文件。
- 不使用 `git add -A`。
- 不在 `main` 上提交。
- 不推 `main`。
- 不 force push。
- 不混合多个模块。
- 不自行创建下一任务实现。
- 自审通过后，可以提交并 push 当前任务分支。

## PR 规则

- base: `main`
- head: 当前任务分支
- PR 内容必须包含：任务范围、测试结果、CC 自审结论、风险、回滚方式
- CC 可以创建 PR 或 draft PR
- CC 不 self-merge
- 高风险任务、失败测试、范围不确定或用户要求时，PR 前召回 Codex 复核

## Codex 复核触发条件

- 用户明确要求 Review
- CC 标记需要外部复核
- 高风险变更已经用户确认但仍需独立审查
- 测试证据不足
- PR 合并前需要额外风险判断
