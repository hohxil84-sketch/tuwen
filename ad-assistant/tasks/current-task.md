# Git 远端同步提交护栏

## 状态

`COMPLETED`

## 分支

`codex/add-precommit-remote-sync`

## 背景与目标

当前 Git 流程要求检查工作区、从 `main` 创建任务分支并在自审后提交，但没有强制读取远端状态。多代理协作时可能基于过期主线开发，或直到推送阶段才发现远端分支已经前进。

本任务为 CC 增加明确的远端同步护栏：开始任务、提交前和推送前必须执行只读远端同步与差异检查；远端不可达或远端分支领先时不得继续提交或推送。

## What To Build

1. 在开始开发前要求执行 `git fetch origin --prune`，失败时停止并报告。
2. 新任务分支必须基于最新 `origin/main` 创建；不得默认本地 `main` 已同步。
3. 提交前再次 fetch，并检查当前分支与其远端跟踪分支的领先/落后状态。
4. 推送前再次确认远端状态；远端领先时先采用明确的 rebase 或 merge 方案同步。
5. 明确禁止在存在未提交改动时盲目执行 `git pull`，禁止自动使用会产生意外合并提交的 pull。
6. 更新项目 Git 工作流、Agent Git 护栏、CC 执行规则和进度记录。

## What Not To Build

- 不修改 CI、GitHub Actions 或部署配置。
- 不自动合并、变基或强制推送。
- 不修改业务代码、数据库、API、Provider、认证、扣费或 Tauri 配置。
- 不提交现有无关未跟踪文件。

## Allowed Files

- `tasks/current-task.md`
- `CLAUDE.md`
- `docs/16-git-workflow.md`
- `docs/20-agent-git-guardrails.md`
- `PROGRESS.md`

## Forbidden Files

- `.github/**`
- `cloud-backend/**`
- `desktop-app/**`
- `official-website/**`
- `shared/**`
- 依赖与 lockfile
- `tasks/residual-risk-tasks.md`

## Acceptance Criteria

- [x] 开始任务前强制 fetch，失败即停止。
- [x] 新分支明确基于最新 `origin/main`。
- [x] 提交前和推送前均检查远端分支差异。
- [x] 远端领先时禁止直接提交或推送。
- [x] 明确禁止脏工作区盲目 pull 和意外 merge commit。
- [x] 三份正式规则表述一致。
- [x] `git diff --check` 通过。

## 完成摘要

已在项目 Git 工作流、Agent Git 护栏和 CC 执行规则中加入远端 fetch、最新主线建分支、upstream 差异检查、失败阻断及禁止脏工作区盲目 pull 的统一规则。

## Test Method

```bash
rg -n "git fetch origin --prune|origin/main|git rev-list --left-right --count|git pull" CLAUDE.md docs/16-git-workflow.md docs/20-agent-git-guardrails.md
git diff --check
git status --short --branch
git diff --cached --name-status
```

## Dependency Permission

不允许新增或升级依赖。

## Major Change Status

`NOT_MAJOR`

仅修改项目协作和 Git 操作文档，不修改 CI、部署或运行时行为。

## Security Requirements

- 不记录或修改 GitHub Token、SSH Key 或其他凭据。
- 远端不可达或认证失败时停止，不绕过验证。
- 不允许 force push。

## Rollback Plan

Revert 本任务提交，恢复原 Git 流程文档。

## Completion Output Required

- 修改文件与规则摘要
- 实际验证命令和结果
- reviewer-mode 自查结论
- 残余风险和回滚方式
- commit hash
