# Development Record

## 2026-05-31

### Sprint-02 Task-04 Mock AI API Endpoint

- Branch: `feature/sprint-02-task-04-mock-ai-api`
- PR: #13
- Merge commit: `0cc7f14`
- Feature commit: `6a40445`
- Scope: added protected `POST /api/v1/mock-ai/ad-copy`.
- Key behavior: auth/device protected, checks plan and `mock_ad_copy`, calls `MockProvider` through `execute_provider_call`, writes `provider_call_log`, propagates `X-Request-ID`, returns unified wrapper.
- Safety: no real Provider SDK, no API key, no network call, no DDL, no dependency change, no frontend/desktop change, no `credit_ledger` write.
- Tests: `21 passed, 1 warning` focused; `147 passed, 1 warning` backend regression; PR #13 `pg-integration` passed.

### Agent Rules Update

- Branch: `docs/rules`
- PR: #14
- Merge commit: `8fa3440`
- Commit: `0e864b7`
- Scope: added communication and Git note rules for Codex / Claude Code / DeepSeek.
- Rules: address user as "大哥"; commit/push/PR/handoff notes use Chinese and English bilingual notes; Codex Review output includes CC-forwardable next-step instructions in Chinese.
- Tests: PR #14 `pg-integration` passed.
