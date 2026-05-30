---
name: ad-assistant-provider-cost-review
description: Provider and AI cost review for the AI 图文广告助手 project. Use when reviewing model routing, provider files, provider_call_log, estimated_cost, credits_charged, AI credit deduction, cost reports, OCR/image/vector providers, or any AI feature implementation.
---

# AI 图文广告助手 Provider Cost Review

## Read First

Read:
- `docs/06-provider-architecture.md`
- `docs/07-ai-cost-control.md`
- `docs/19-pricing-and-credit-system.md`
- `docs/12-database-design.md`
- `tasks/current-task.md`

## Blocking Findings

Block commit if:
- frontend directly calls a third-party AI API
- API keys are sent to desktop or browser clients
- AI calls bypass cloud Provider layer
- provider calls do not write `provider_call_log`
- credit deduction happens on client
- feature cost is hardcoded as fixed points without provider cost basis
- unlimited AI membership behavior is introduced
- Provider interface changes without confirmation

## Required Provider Evidence

For every cloud AI call, verify:
- provider
- model
- feature
- request_id
- user_id
- device_id
- raw usage or equivalent
- estimated_cost
- credits_charged
- status
- error_code when failed

## Routing Check

Confirm:
- normal tasks prefer DeepSeek
- advanced tasks use GPT or Claude only when authorized
- image tasks route by quality and cost
- local providers do not bypass authorization

## Output

Report:
- blocking cost or provider issues
- cost traceability gaps
- missing log fields
- routing concerns
- whether commit is allowed

