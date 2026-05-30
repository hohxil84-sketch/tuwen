---
name: ad-assistant-api-db-review
description: API contract and database review for the AI 图文广告助手 project. Use when reviewing FastAPI endpoints, OpenAPI, shared DTO, TypeScript types, database models, migrations, indexes, usage_events, provider_call_log, credit_ledger, or schema changes.
---

# AI 图文广告助手 API and DB Review

## Read First

Read:
- `docs/05-api-contract.md`
- `docs/12-database-design.md`
- `docs/15-coding-standards.md`
- `docs/20-agent-git-guardrails.md`
- `tasks/current-task.md`

## Major Change Stop Rule

Database schema changes, OpenAPI changes, shared DTO changes, and API contract changes require user confirmation before implementation.

If already changed without confirmation, mark as blocking.

## API Checklist

Verify:
- unified response shape
- stable error codes
- request_id propagation
- no client-submitted final plan, final credit charge, or provider cost
- auth and device checks on protected endpoints
- shared DTO and OpenAPI stay consistent

## Database Checklist

Verify:
- migrations are explicit and reversible
- sensitive fields are hashed or encrypted
- credit changes write ledger rows
- provider calls write `provider_call_log`
- usage events are separate from billing decisions
- indexes exist for expected query paths

## Output

Report:
- contract breaks
- migration risks
- data integrity issues
- missing tests
- whether commit is allowed

