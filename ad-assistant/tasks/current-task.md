# Current Task: Agent Workflow CC Autonomous Handoff

## Status

`IMPLEMENTED_SELF_REVIEW_READY`

Implementation completed on 2026-06-01. Ready for commit and PR.

Suggested branch: `docs/cc-autonomous-workflow`

## Background

The project workflow is changing from Codex-led task writing and mandatory Codex Review to a CC-first process:

- Claude Code / DeepSeek should own task writing, implementation, testing, self-review, task-branch commit/push, and PR preparation.
- Codex should be optional and invoked only for high-risk, unclear, failing, or user-requested review cases.
- Bug fixes must be root-cause driven before code changes.
- Module progress must be tracked in a root-level `PROGRESS.md`.

## Goal

Update project rules and local skills so CC can independently execute the full development loop while preserving high-risk stop rules and PR merge guardrails.

## What To Build

1. Update project workflow docs to define CC autonomous responsibilities.
2. Update Git guardrails so CC self-review is the default commit gate.
3. Add `PROGRESS.md` as the module progress ledger.
4. Require CC to update `PROGRESS.md` after each module or task.
5. Require bug fixes to follow: reproduce/confirm, root cause, solution plan, implementation, tests, feedback.
6. Update local Codex skills used by this project so they no longer conflict with the new CC-first rules.

## What Not To Build

- No business feature work.
- No backend, desktop, official website, shared DTO, API, database schema, provider, auth, credit, payment, Tauri, CI, dependency, or lockfile changes.
- No direct push to `main`.
- No self-merge.

## Allowed Files

- `README.md`
- `CLAUDE.md`
- `CODEX.md`
- `PROGRESS.md`
- `docs/14-ai-agent-workflow.md`
- `docs/16-git-workflow.md`
- `docs/20-agent-git-guardrails.md`
- `tasks/current-task.md`
- Local skill files under `C:\Users\123\.codex\skills\ad-assistant-task-executor\`
- Local skill files under `C:\Users\123\.codex\skills\ad-assistant-git-guardrails\`

## Forbidden Files

- `cloud-backend/**`
- `desktop-app/**`
- `official-website/**`
- `shared/**`
- `cloud-backend/migrations/**`
- `.github/workflows/**`
- dependency manifests and lockfiles
- `.env` and `.env.example`
- unrelated task draft files

## Acceptance Criteria

1. Project docs consistently describe CC as the default task writer, implementer, tester, self-reviewer, task-branch committer/pusher, and PR preparer.
2. Codex Review is described as optional/on-demand, not a required commit gate.
3. High-risk stop rules remain explicit.
4. Bug fix root-cause workflow is documented.
5. `PROGRESS.md` exists with a reusable entry template.
6. CC is required to update `PROGRESS.md` after every completed module or task.
7. Local project skills match the new workflow.
8. `git diff --check` passes.
9. Skill validation passes for modified skills.

## Test Method

```powershell
git diff --check
python C:\Users\123\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\123\.codex\skills\ad-assistant-task-executor
python C:\Users\123\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\123\.codex\skills\ad-assistant-git-guardrails
```

## Dependency Permission

No dependency changes are allowed.

## Major Change Status

No code or infrastructure major change. This is a workflow and documentation change.

High-risk operational rules are changed intentionally:

- CC self-review becomes the default commit gate.
- Codex Review becomes optional/on-demand.
- CC may commit and push task branches after self-review.

`main` remains protected by PR-only merge and no self-merge rules.

## Security Requirements

- Do not add secrets, API keys, tokens, production connection strings, or private user data.
- Preserve high-risk stop rules for auth, token, provider, credit, payment, Tauri, CI, dependencies, and database changes.

## Rollback Plan

Revert the documentation and skill updates from the workflow commit. No database or dependency rollback is required.

## Completion Output Required

- Changed files
- Implemented scope
- Not implemented scope
- Self-review result
- Test commands and results
- `PROGRESS.md` status
- Skill validation result
- Risks and rollback
- Commit hash and PR link
