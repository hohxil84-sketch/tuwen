# Current Task: Sprint-02 Task-06 Desktop Mock AI E2E Smoke Verification

## Status

`CONFIRMED_READY_FOR_IMPLEMENTATION`

Prepared after Sprint-02 Task-05 was merged by PR #16 as `42dbad8`.

User confirmed this task sheet on 2026-06-01. Implementation may start on the suggested task branch, but must stay within this task scope and wait for Codex Review before commit.

## Suggested Branch

`feature/sprint-02-task-06-desktop-mock-e2e-smoke`, based on latest `main`.

If a local Git ref permission or slash-name issue occurs, use the flat branch name `sprint-02-task-06-desktop-mock-e2e-smoke`.

## Prerequisites

- Latest verified `main`: `42dbad8` (`Merge pull request #16 from hohxil84-sketch/feature/sprint-02-task-05-desktop-mock-ai-client`).
- Sprint-02 Task-05 Desktop Mock AI API Client was merged by PR #16.
- Desktop app now has:
  - cloud API client;
  - memory-only auth store;
  - login UI;
  - login-gated Mock AI ad-copy panel on the OCR page.
- Cloud backend already has:
  - auth/device APIs;
  - `POST /api/v1/mock-ai/ad-copy`;
  - `provider_call_log`;
  - PostgreSQL integration CI.
- Task-05 residual risk: live manual verification was not completed because the local environment did not have PostgreSQL/backend service ready.

## Background

The project now has enough pieces for a visible mock MVP path, but the full local desktop-to-cloud flow has not been manually verified:

1. start cloud backend with PostgreSQL;
2. start desktop Vite app;
3. login with a valid user and device fingerprint;
4. submit Mock AI ad-copy request;
5. confirm request_id/provider/model/credits display;
6. confirm memory-only token behavior after refresh;
7. confirm existing local OCR UI still works.

This task is a verification and local bring-up slice. It should make the already-implemented mock flow reproducible for development review before real provider work begins.

## Major Change Proposal

This task may add a narrow local development runbook and, only if necessary, a dev-only seed helper for local test users/devices.

1. Reason
   - Remove the current manual-verification gap from Task-05.
   - Make the desktop mock MVP path visible and repeatable on a developer machine.
   - Avoid starting real provider or billing work before the current mock integration is proven end-to-end.

2. Risks
   - Dev seed helpers could accidentally look like production account-management code.
   - Local setup docs could encourage insecure defaults if not clearly marked dev-only.
   - Manual verification could drift if commands are not recorded precisely.

3. Impact
   - Documentation and verification evidence.
   - Optional dev-only seed/run helper if existing commands are insufficient.
   - No product feature expansion.
   - No API contract, database schema, provider, credit, payment, shared DTO, Tauri permission, or dependency changes.

4. Rollback
   - Remove the new runbook/context documentation.
   - Remove any dev-only helper added by this task.
   - No database rollback is required if no schema changes are made.

5. Backward Compatibility
   - Compatible. Existing APIs and desktop UI behavior remain unchanged.

6. Database Migration
   - None. This task must not add, remove, or edit migrations or DDL.

## What To Build

### 1. Local runbook for the mock desktop MVP path

Add or update documentation with exact local commands for:

- starting PostgreSQL for development;
- setting required backend environment variables, including a non-default `JWT_SECRET_KEY`;
- applying existing database setup/migrations if required by the current backend;
- starting the cloud backend;
- starting the desktop Vite app;
- configuring `VITE_CLOUD_API_BASE_URL` if needed;
- starting local OCR service only if needed for OCR verification.

### 2. Dev-only test user/device setup path

If the repo already has a safe way to create a local test user and bound device, document it.

If no safe path exists, CC may add a narrow dev-only helper, but must stop and report before doing so if it requires touching files outside the allowed list.

Rules:

- must be clearly marked development-only;
- must not create production admin flows;
- must not add registration, password reset, subscription, payment, recharge, or account-management UI;
- must not store real secrets;
- must not bypass backend auth/device checks in production code.

### 3. Manual E2E smoke verification

Run and record:

1. cloud backend starts successfully;
2. desktop dev server starts successfully;
3. login succeeds with a valid local test user and device fingerprint;
4. Mock AI panel becomes visible after login;
5. mock ad-copy request succeeds;
6. UI displays `provider=mock`, `model=mock-text-v1`, `credits_charged=0`, and a backend `request_id`;
7. page refresh clears token state;
8. existing OCR upload/recognition/history path is either verified against local OCR service or explicitly marked blocked with exact reason.

### 4. Update module context and sprint docs

Update:

- `docs/25-desktop-mock-e2e-smoke.md`
- `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md`
- `docs/09-desktop-app-guide.md`
- `docs/11-cloud-backend-guide.md`
- `docs/sprint-02-summary.md`
- `tasks/current-task.md`

## What Not To Build

- Do not add real OpenAI, DeepSeek, Claude, ComfyUI, OCR, image, vector, or local provider calls.
- Do not add provider SDKs, dependencies, API keys, or third-party AI network calls.
- Do not implement real provider routing or model selection.
- Do not implement real credit deduction or `credit_ledger` consumption.
- Do not add payment, recharge, order, grant, monthly quota, expiration, admin, invoice, registration, password reset, or subscription flows.
- Do not modify API contracts, OpenAPI, shared DTOs, cloud backend auth/token algorithms, Provider interfaces, credit services, DDL, migrations, Tauri permissions, CI workflows, or dependency files.
- Do not persist desktop tokens.
- Do not create a generic prompt execution UI.
- Do not modify official website code.

## Allowed Files

Implementation task may modify only:

- `docs/25-desktop-mock-e2e-smoke.md` (new)
- `docs/module-context/sprint-02-task-06-desktop-mock-e2e-smoke/context.md` (new)
- `docs/09-desktop-app-guide.md`
- `docs/11-cloud-backend-guide.md`
- `docs/sprint-02-summary.md`
- `tasks/current-task.md`
- `cloud-backend/docs/*.md` (documentation only)
- `cloud-backend/scripts/dev_seed_user.py` (new, optional, dev-only, only if needed)

If implementation proves another file is required, CC must stop and report why before modifying it.

## Forbidden Files

Do not modify:

- `cloud-backend/app/**`
- `cloud-backend/migrations/**`
- `cloud-backend/tests/**`
- `shared/**`
- `official-website/**`
- `.github/workflows/**`
- `desktop-app/src/**`
- `desktop-app/src-tauri/**`
- `desktop-app/local-service/**`
- `desktop-app/local-tools/**`
- `desktop-app/migrations/**`
- dependency files or lockfiles
- `.env` or `.env.example`
- files containing secrets

## Acceptance Criteria

- The merged Task-05 desktop mock flow is manually verified end-to-end, or every blocked step has a concrete environment reason.
- The runbook contains exact commands that another agent can follow.
- Dev-only setup is clearly separated from production behavior.
- No backend product code, API contract, DDL, dependency, shared DTO, Tauri, Provider, credit, or desktop source code changes are made.
- No real provider keys/SDKs/network calls are added.
- `npm run build` passes in `desktop-app`.
- `git diff --check` passes.
- Module context is updated with verification facts and residual risks.

## Test Method

Desktop build:

```bash
cd D:/Project/ad-assistant/desktop-app
npm run build
```

Whitespace check:

```bash
cd D:/Project/ad-assistant
git diff --check
```

Manual smoke:

```text
1. Start local PostgreSQL/backend using the documented runbook.
2. Start desktop Vite dev server.
3. Login with the documented local test user/device fingerprint.
4. Submit a Mock AI ad-copy request.
5. Confirm mock result fields and request_id.
6. Refresh and confirm tokens are gone.
7. Verify OCR flow or record the exact local OCR blocker.
```

## Dependency Permission

No new dependencies are allowed.

Do not edit dependency files or lockfiles.

## Major Change Status

Yes, only if a dev seed helper is added. It must remain local-development-only and must not change production auth, device binding, API contract, schema, or security behavior.

User confirmation of this task sheet is required before implementation.

## Security Requirements

- Do not store real secrets in repo.
- Do not write `.env` files with secrets.
- Do not bypass backend auth/device checks.
- Do not persist desktop tokens.
- Do not add client-side provider/model/cost/credit decisions.
- Keep all seed/test credentials clearly marked as local development only.

## Review Instructions For Codex

Review Sprint-02 Task-06 Desktop Mock AI E2E Smoke Verification.

Focus on:

1. whether the manual verification evidence is complete and reproducible;
2. whether any dev seed helper is strictly dev-only;
3. whether no production backend/desktop/API/DDL/dependency changes were made;
4. whether no secrets or real provider keys were added;
5. whether residual manual blockers are concrete and actionable.

Output:

- blocking issues;
- high-risk issues;
- medium/low-risk issues;
- verification conclusion;
- whether commit is allowed.

## Completion Output Required

Implementer must report:

- changed files;
- exact runbook commands added or used;
- exact build/check commands and results;
- manual verification steps and results;
- confirmation that no production backend/API/DDL/dependency/shared/Tauri/desktop source changes were made;
- confirmation that no secrets or real provider integrations were added;
- residual risks;
- whether module context was updated;
- wait for Codex Review, do not self-merge.
