---
name: ad-assistant-security-review
description: Security review for the AI 图文广告助手 project. Use when reviewing authentication, authorization, device binding, token storage, Tauri permissions, local FastAPI services, logs, anti-crack controls, API keys, rate limits, risk logs, or any code before commit.
---

# AI 图文广告助手 Security Review

## Read First

Read:
- `CODEX.md`
- `docs/08-security-and-anti-crack.md`
- `docs/09-desktop-app-guide.md`
- `docs/11-cloud-backend-guide.md`
- `docs/20-agent-git-guardrails.md`
- `tasks/current-task.md`

## Blocking Findings

Block commit if any of these exist:
- API Key in client code
- frontend directly calls third-party AI APIs
- client deducts credits
- client decides plan, authorization, or premium access
- plaintext password, token, refresh token, or provider key storage
- bypassable cloud authorization
- unconfirmed auth, token, Tauri permission, filesystem permission, or local service startup change
- new remote command execution capability
- sensitive data in logs

## Review Checklist

Check:
- access token lifetime and refresh flow
- refresh token storage and revocation
- device binding enforced by cloud
- offline license cache is signed and time-limited
- rate limiting is present or explicitly planned
- risk logs are written for security events
- local service validates paths, file types, sizes, and timeouts
- logs are redacted

## Output

Lead with findings by severity:
- blocking
- high risk
- medium or low risk
- test gaps
- whether commit is allowed

