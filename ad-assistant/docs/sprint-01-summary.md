# Sprint-01 Summary

Date: 2026-05-31
Base branch: `main`
Current verified head: `96078ba fix(usage): use is-not-None guard for estimated_cost serialization`

## Completed Modules

| Task | Scope | Main merge / commit |
|------|-------|---------------------|
| Task-01 | Project skeleton | `0cfa63c feat(scaffold): add Sprint-01 project skeleton` |
| Task-02 | Auth/Device implementation plan | `b8a0be6 docs(auth): Auth/Device implementation plan with confirmed decisions (#2)` |
| Task-03 | Auth/Device implementation | `56aadb2 Merge pull request #3 from hohxil84-sketch/feature/sprint-01-auth-device` |
| Task-04 | Local OCR minimal loop | `599e2b0 feat(ocr): add local OCR minimal loopFeature/sprint 01 ocr minimal (#4)` |
| Task-05 | `usage_events` and `provider_call_log` foundation | `d36cd78 feat(usage): add usage events and provider call log foundation (#5)` |
| Task-05 fix | Preserve `estimated_cost=0` during serialization | `96078ba fix(usage): use is-not-None guard for estimated_cost serialization` |

## Current Cloud API Capability

- Auth/Device APIs provide the Sprint-01 login, refresh, logout, device bind, and current-device foundation.
- `GET /api/v1/usage/events` requires authentication and returns only the current user's usage events.
- `GET /api/v1/usage/events` supports `limit`, `offset`, and `feature`.
- `GET /api/v1/provider-call-logs` requires authentication and returns only the current user's provider call logs.
- `GET /api/v1/provider-call-logs` supports `limit`, `offset`, `feature`, and `status`.
- Usage and provider-log query APIs return the unified `{success, data, error, request_id}` response shape.

## Current Local OCR Capability

- Local FastAPI service exposes `POST /local/ocr` for image upload OCR.
- Local FastAPI service exposes `GET /local/ocr/health`.
- Local FastAPI service exposes `GET /local/ocr/history` and `GET /local/ocr/history/{record_id}`.
- PaddleOCR is wrapped behind the local service with file type, file size, path, timeout, and error-mapping constraints.
- Desktop OCR and history pages call the local OCR service through the frontend OCR service layer.

## Current Data Stores

Cloud backend PostgreSQL DDL files currently define:
- `users`
- `devices`
- `auth_sessions`
- `risk_logs`
- `usage_events`
- `provider_call_log`

Local OCR stores runtime history in SQLite:
- `ocr_history`

The local SQLite database file is runtime data and is not a committed source file.

## Task-05 Verification

- Task-05 backend tests were verified with `pytest tests/ -v`.
- Recorded result: `79 passed`.
- `git diff --check` passed during Task-05 review.
- Task-05 coverage was SQLite ORM tests plus static DDL checks.

## Known Residual Risks

- Task-05 did not run a real PostgreSQL migration integration test.
- DDL rollback is currently documented as commented `DROP TABLE` statements; the migration/rollback system still needs formalization.
- `provider_call_log` is a foundation table and minimal query API only; it does not mean real AI Provider integration is complete.
- `usage_events` is a foundation table and minimal query API only; it does not mean product analytics or reporting is complete.
- Real credit deduction and `credit_ledger` are not implemented.
- Membership, package, payment, recharge, and grant-balance flows are not implemented.
- Backend admin query/reporting capability is not implemented.
- Local OCR history contains user-sensitive OCR content and image metadata; retention, cleanup, and privacy policy still need explicit product decisions.

## Next-Stage Candidate Tasks

These are candidates only. They are not implemented by Sprint-01 Task-06.

- Candidate A: Sprint-02 Task-01 AI credit account and `credit_ledger` foundation table.
- Candidate B: Sprint-02 Task-01 cloud Provider abstraction and mock Provider call.
- Candidate C: Sprint-02 Task-01 PostgreSQL migration/integration test infrastructure.

Before starting the next module, create a new task document, use a new task branch, and keep the scope limited to the confirmed task.
