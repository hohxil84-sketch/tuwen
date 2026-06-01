# 16 Git 工作流

## 基本原则

- 一任务一分支，一模块一分支。
- 开发分支不能是 `main`。
- 只提交当前任务相关文件。
- CC 自审和 reviewer-mode 自查通过后可以提交和 push 当前任务分支。
- `main` 只能通过 PR 合并。

## 开始开发前

1. 运行 `git status --short --branch`。
2. 如果没有有效任务单，先由 Codex 根据用户目标起草或更新 `tasks/current-task.md`。
3. CC 确认任务单有效，且没有自行扩大、重写或弱化 Codex/用户确认的范围。
4. 从 `main` 创建或切换到任务分支。
5. 确认没有未处理的无关改动。
6. 判断是否触碰高风险边界；如果触碰，先等用户确认。

## 提交前

1. 确认只修改当前任务相关文件。
2. 运行任务单要求的测试。
3. 完成 CC 自审清单。
4. 执行 reviewer-mode 自查：停止继续写功能代码，按代码审查标准查找 bug、行为回归、安全/隐私风险、测试缺口、范围越界和高风险边界。
5. 如果 reviewer-mode 发现阻塞或高风险问题，必须先修复、补测、重新运行测试，并再次执行 reviewer-mode；不能把“已自审”当作通过依据。
6. 高风险任务必须在 reviewer-mode 通过后再请求 Codex 复核；CC 自审和 reviewer-mode 不能替代 Codex 高风险复核。
7. 更新模块上下文。
8. 只 stage 当前任务相关文件。
9. 如果工作区存在无关改动，必须运行并展示 `git status --short --branch` 和 `git diff --cached --name-status`。
10. 用户或 Codex 确认 staged 文件列表前，不得提交。

## 提交规则

- 不使用 `git add -A`。
- commit message 必须使用中文，且说明本次任务目的；禁止使用 `update`、`fix`、`changes`、`misc`、`wip` 这类空泛说明。
- 不把无关文件混进同一个 commit。
- 不把多个任务、多个模块或高风险边界改动混进同一个 commit。
- 不提交本地数据库、日志、构建输出、egg-info、临时文件等生成物。
- 不在当前任务 commit 中夹带 package/lockfile、Tauri、backend、OCR、CI 等任务外改动；确需修改时，单独任务、单独分支、单独提交。
- 不在 `main` 上提交。
- 不 `git push origin main`。
- 不 force push。
- 提交目标只能是当前任务分支。
- 推送命令只能指向当前任务分支，例如 `git push -u origin <current-branch>`。

## PR 规则

- PR base 为 `main`。
- PR head 为当前任务分支。
- PR title 和 PR body 必须使用中文。
- PR 内容必须包含任务范围、修改摘要、测试结果、CC 自审结论、reviewer-mode 自查结果、风险和回滚方式。
- 高风险任务、失败测试、范围不确定或用户要求时，PR 前召回 Codex 复核。

## 合并规则

- CC 不能未经用户明确确认 self-merge。
- 用户明确确认某个 PR 可以合并后，CC 可以通过 GitHub PR 合并该 PR。
- PR 合并也可由用户、仓库管理员或明确授权的流程完成。
- 合并前必须有任务单、测试记录、CC 自审结论和风险说明。
- 合并后必须用中文交付说明记录用户确认来源、PR 编号、合并方式、合并结果和后续注意事项。

## 相关规则

更详细的守卫规则见 `docs/20-agent-git-guardrails.md`。
