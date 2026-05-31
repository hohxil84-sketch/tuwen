# Module Context: Sprint-02 Task-06 Desktop Mock AI E2E Smoke Verification

## Status

`CONFIRMED_READY_FOR_IMPLEMENTATION`

Prepared after Sprint-02 Task-05 was merged to `main` by PR #16.

User confirmed the Task-06 task sheet on 2026-06-01.

## Base

- Latest verified `main`: `42dbad8`
- Previous task: Sprint-02 Task-05 Desktop Mock AI API Client
- Previous feature commit: `89b901a`
- Previous merge commit: `42dbad8`

## Goal

Make the merged desktop mock MVP path reproducible and manually verified:

```text
cloud backend + PostgreSQL -> desktop login -> Mock AI ad-copy request -> visible mock result
```

## Why This Exists

Task-05 passed code review and build checks, but live manual verification remained blocked because the local environment did not have PostgreSQL/backend service ready.

Before real provider or billing work begins, the project needs one small verification slice that proves the current mock path can be started, used, and inspected on a developer machine.

## Expected Scope

- Local runbook for cloud backend + desktop app startup.
- Local development test user/device setup path.
- Manual smoke verification evidence for login, Mock AI result, request_id display, memory-only token refresh behavior, and OCR path status.
- Documentation only by default.
- Optional dev-only seed helper only if existing commands are insufficient.

## Forbidden Expansion

Do not add:

- real provider routing;
- real OpenAI/DeepSeek/Claude/ComfyUI calls;
- provider SDKs or API keys;
- real credit deduction;
- payment, recharge, registration, password reset, admin, or subscription flows;
- API contract, DDL, migration, shared DTO, Tauri permission, dependency, CI, or production auth changes;
- desktop source changes.

## Review Notes

Codex should review this task mainly as a reproducibility and safety task:

- Are commands exact enough for another agent to run?
- Are any seed/test credentials clearly local-development-only?
- Did the task avoid production behavior changes?
- Is every failed manual step backed by a concrete blocker?
