---
name: ad-assistant-git-guardrails
description: Git workflow and pre-commit guardrails for the AI 图文广告助手 project. Use before staging, committing, pushing, opening PRs, reviewing branches, or checking whether Claude Code, DeepSeek, or Codex may commit changes.
---

# AI 图文广告助手 Git Guardrails

## Read First

Read:
- `docs/16-git-workflow.md`
- `docs/20-agent-git-guardrails.md`
- `CODEX.md`
- `CLAUDE.md`
- `tasks/current-task.md`

## Commit Rule

Every commit requires Codex Review first.

Do not commit when:
- there is no valid task
- task scope is exceeded
- tests are missing without explanation
- major changes lack confirmation
- Codex Review has not explicitly allowed commit
- secrets are present
- BACKLOG, FUTURE, or BLOCKED functionality was implemented

## Branch Rule

Use one branch per task and module.

Do not mix unrelated modules in one branch.

## Pre-Commit Review Steps

Check:
- changed file list
- task allowlist and denylist
- major-change protected paths
- secrets and API keys
- tests run
- Codex Review conclusion

## Output

Give a clear decision:
- allow commit
- block commit
- required fixes before commit

Include the exact reason when blocking.

