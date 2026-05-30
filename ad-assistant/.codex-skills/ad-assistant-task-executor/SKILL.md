---
name: ad-assistant-task-executor
description: Execute approved development tasks for the AI 图文广告助手 project. Use when Codex or another agent is asked to implement work in this monorepo, especially tasks governed by tasks/current-task.md, module branch rules, file allowlists, forbidden future features, and Claude Code + DeepSeek execution boundaries.
---

# AI 图文广告助手 Task Executor

## Required Context

Before making changes, read:
- `README.md`
- `CODEX.md`
- `CLAUDE.md`
- `tasks/current-task.md`
- Relevant `docs/*.md`

## Execution Rules

Only implement what `tasks/current-task.md` explicitly allows.

Do not implement:
- BACKLOG, FUTURE, or BLOCKED functionality
- features not listed in the current task
- major changes that lack user confirmation

If the task is missing any of these fields, stop and ask for a valid task:
- what to develop
- what not to develop
- allowed files
- forbidden files
- acceptance criteria
- test method
- dependency permission
- major-change status

## Major Change Stop Rule

Stop before changing:
- database schema
- API contract
- Provider interface
- auth or token logic
- credit or payment logic
- shared DTO
- OpenAPI
- Tauri permissions
- auto-update logic
- local Python service startup
- filesystem permissions
- remote command execution ability
- core dependencies

Output the required major-change proposal and wait for confirmation.

## Completion Output

Report:
- modified files
- implemented scope
- not implemented scope
- test commands and results
- risks
- whether major changes were touched
- that Codex Review is required before commit

