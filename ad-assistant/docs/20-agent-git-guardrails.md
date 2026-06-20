# 20 Agent Git 约束

## 适用场景

当需要判断能否提交、推送、建 PR，或确认当前任务的 Git 流程是否合规时，使用本规则。

## 默认门禁

CC 自审是默认提交门禁的第一步，不是最终质量门禁。CC 自审完成后必须追加 reviewer-mode 自查；Codex Review 是按需复核，不再是每次提交的强制条件，但高风险任务必须在 reviewer-mode 通过后再请求 Codex 复核。

进入提交前，CC 必须确认：

- 当前开发分支不是 `main`
- 已成功运行 `git fetch origin --prune`；没有使用缓存的远端引用代替本次检查
- 新任务分支基于最新 `origin/main` 创建
- 当前分支的远端跟踪分支没有本地缺失提交
- 当前任务单有效；没有有效任务单时，CC 已暂停并请求 Codex/用户起草或更新 `tasks/current-task.md`
- 只修改当前任务相关文件
- 未自行扩大、重写或弱化 Codex/用户确认的任务单范围
- 没有混入无关文件
- 没有未确认的高风险变更
- 没有 secrets、真实密钥、Token 或生产连接串
- 测试已运行并记录结果
- 模块上下文已更新
- `PROGRESS.md` 已追加更新
- `tasks/current-task.md` 未被写入详细实现报告；如有更新，仅限状态、分支、简短完成摘要、commit/PR 信息
- 自审清单已完成
- reviewer-mode 自查已完成，且阻塞/高风险发现已修复
- commit message、PR title、PR body 和交付说明均已准备中文说明

## Reviewer-mode 自查门禁

完成实现和常规自审后，CC 必须停止继续写功能代码，切换到 reviewer-mode 审查自己的改动。审查重点是 bug、行为回归、安全/隐私风险、测试缺口、范围越界、未处理的高风险边界和 staged 文件污染。

Reviewer-mode 输出必须 findings first，并按严重程度排序。没有发现问题时，也必须明确写出“未发现阻塞问题”和剩余风险/测试缺口。若 reviewer-mode 发现阻塞或高风险问题，本次自审视为未通过，必须先修复、补充必要测试、重新运行相关测试，并再次执行 reviewer-mode。

Reviewer-mode 结果必须记录：审查范围、发现的问题、已修复内容、未修复风险、测试缺口、实际运行的测试命令和结果、`git status --short --branch`、`git diff --cached --name-status`。

高风险任务必须在 reviewer-mode 通过后再请求 Codex 复核。高风险范围包括但不限于数据库 schema/DDL/migration、API contract/OpenAPI/shared DTO、Provider/模型路由/真实 AI 调用、Auth/Token/权限、Credit/Payment/扣费/provider cost、Tauri 权限、本地服务启动、文件系统权限、CI/依赖/环境变量、删除/清空/清理用户数据或沙箱文件。

## 必须暂停的情况

- 没有有效任务单，且 CC 准备绕过 Codex/用户确认直接写代码或提交
- 任务范围超出 allowed files 且无法证明必要性
- 触碰 DDL、API、Provider、Auth/Token、credit、payment、Tauri、dependency、CI、security 等边界但没有用户确认
- 存在 secrets 或真实密钥
- 测试失败且无法在当前任务范围内修复
- bug 根因不明确却准备直接改代码
- 当前分支是 `main`
- `git fetch origin --prune` 因网络、认证或权限问题失败
- 当前分支的远端跟踪分支存在本地缺失提交，但尚未确定同步方案
- 需要删除文件、重命名目录或做大规模重构
- 需要安装到本机的桌面级应用，但未安装到 `D:\APPLICATION`
- 需要安装到本机的环境依赖、SDK、CLI、运行时、模型、缓存、构建工具或其他外部工具，但未安装/配置到 `D:\locaPath`
- 工具链或安装器强制写入 `C:` 盘，且 CC 尚未说明原因、占用空间、风险、清理方式并取得用户确认

## 执行规则

- 开始任务、提交前和推送前都必须运行 `git fetch origin --prune`；任一次失败都必须停止，不能继续使用旧的远端引用。
- 新任务分支必须使用最新 `origin/main` 作为起点，例如 `git switch -c <task-branch> origin/main`。
- 当前分支已有 upstream 时，提交前和推送前必须运行 `git rev-list --left-right --count "HEAD...@{upstream}"`；右侧计数大于 0 时不得提交或推送。
- 当前分支没有 upstream 时，必须确认远端不存在同名分支，或先建立并检查正确的 upstream。
- 不得在存在未提交改动时盲目执行 `git pull`；同步前必须保护并检查本地改动，明确选择 rebase 或 merge，禁止由默认 pull 行为产生意外合并提交。
- 只 stage 本任务相关文件。
- 不使用 `git add -A`。
- 如果工作区存在无关改动，提交前必须展示：
  - `git status --short --branch`
  - `git diff --cached --name-status`
- 在用户或 Codex 明确确认 staged 文件列表前，不得提交。
- staged 文件只能包含当前任务单 allowed files 中的文件，或任务单中已明确批准的必要例外。
- 如果 staged 文件包含 unrelated files、generated files、local databases、logs、依赖/lockfile、Tauri、backend、OCR、CI 等任务外文件，必须停止并取消 stage。
- `tasks/current-task.md` 不是完成报告；不得把详细实现记录、测试输出、自审全文、reviewer-mode 全文或合并记录写入任务单正文顶部。
- 不得把多个任务的改动拆不开地塞进同一个 commit；需要拆分时，先切换或创建对应任务分支。
- `git commit` 必须使用中文提交说明，且说明本次任务目的；禁止使用 `update`、`fix`、`changes`、`misc`、`wip` 这类空泛说明。
- 不在 `main` 上提交。
- 不推 `main`。
- 不 force push。
- 不混合多个模块。
- 不自行创建下一任务实现。
- 新增桌面级应用时，默认安装到 `D:\APPLICATION`；新增环境依赖、SDK、CLI、运行时、模型、缓存或构建工具时，默认安装/配置到 `D:\locaPath`；交付说明必须写明实际安装位置和缓存位置。
- 不得默认把新工具、桌面应用、依赖缓存、模型缓存或大体积构建缓存安装到 `C:` 盘；如无法避免，必须先暂停并等待用户确认。
- 自审和 reviewer-mode 自查均通过，且远端同步门禁通过后，可以提交并 push 当前任务分支。

## PR 规则

- base: `main`
- head: 当前任务分支
- PR title 和 PR body 必须使用中文
- PR 内容必须包含：任务范围、修改摘要、测试结果、CC 自审结论、reviewer-mode 自查结果、风险、回滚方式
- CC 可以创建 PR 或 draft PR
- CC 不能未经用户明确确认 self-merge
- 用户明确确认某个 PR 可以合并后，CC 可以通过 GitHub PR 合并该 PR，并用中文记录确认来源、PR 编号、合并方式、合并结果和后续注意事项
- 高风险任务、失败测试、范围不确定或用户要求时，PR 前召回 Codex 复核；CC 自审和 reviewer-mode 自查不能替代 Codex 高风险复核

## Codex 复核触发条件

- 用户明确要求 Review
- CC 标记需要外部复核
- 高风险变更已经用户确认但仍需独立审查
- 测试证据不足
- PR 合并前需要额外风险判断
