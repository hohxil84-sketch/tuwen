# Current Task: Sprint-03 Task-04 Desktop Dashboard UI Redesign

## Status

`READY_FOR_CC_IMPLEMENTATION`

## Background

The desktop app front page needs a visual redesign before additional backend features are connected.

The target direction is a dark SaaS-style desktop workbench based on the user's reference image: fixed left navigation, top status bar, dashboard cards, quick function entries, recent orders, recent generated images, and bottom connection/version status.

Implementation must follow:

- `docs/26-desktop-dashboard-ui-redesign.md`

## Completed Context

Sprint-03 Task-02 (DeepSeek Provider) merged via PR #32 @ `1773ab4`.

Sprint-03 Task-03 (Real Credit Deduction) implemented, awaiting Codex Review.

## This Task Develops

- Desktop dashboard UI shell only.
- New or updated dashboard page for the desktop app home route.
- Dark workbench layout with:
  - left sidebar navigation,
  - top status bar,
  - welcome card,
  - usage/stat cards,
  - quick entry cards,
  - recent orders mock table,
  - recent generated images mock grid,
  - bottom status bar.
- Frontend mock data for dashboard display.
- Route behavior so `/` opens the dashboard page.
- Existing `/login`, `/ocr`, and `/history` routes remain accessible.
- OCR quick entry should navigate to the existing OCR page.
- Unimplemented feature entries must be clearly marked as disabled, "coming soon", or equivalent placeholder behavior.

## This Task Does Not Develop

- No backend API integration.
- No database schema or migration work.
- No real AI provider calls.
- No real credit deduction logic.
- No authentication redesign.
- No OCR business-logic rewrite.
- No Tauri packaging or installer work.
- No Docker-based local services.
- No local database/cache/service startup for dashboard mock data.

## Allowed Files

Primary allowed scope:

- `desktop-app/src/App.vue`
- `desktop-app/src/router.ts`
- `desktop-app/src/pages/**`
- `desktop-app/src/components/**`
- `desktop-app/src/stores/**` only if needed for existing auth display without changing auth semantics
- `desktop-app/src/assets/**` only for local UI assets if needed
- `docs/26-desktop-dashboard-ui-redesign.md` only for small clarifications if implementation discovers an ambiguity
- `tasks/current-task.md` only for status updates

Package files are not expected to change. If CC believes a new dependency is required, stop and ask before changing package files.

## Forbidden Files

Do not modify:

- `cloud-backend/**`
- `shared/**`
- database migrations or schema files
- provider implementation files
- credit/billing logic
- real authentication or authorization semantics
- Tauri packaging/configuration files unless the user explicitly creates a separate Tauri task
- Docker files or Docker Compose files
- unrelated docs

Do not clean up unrelated current working tree changes.

## Acceptance Criteria

- Desktop home page visually matches the direction in `docs/26-desktop-dashboard-ui-redesign.md`.
- The app uses a dark desktop workbench shell instead of a simple top-link layout.
- Left navigation, top status bar, dashboard cards, quick entries, recent orders, recent generated images, and bottom status bar are visible.
- Dashboard data is mock frontend data and works offline.
- `/` opens the dashboard.
- `/login`, `/ocr`, and `/history` remain accessible.
- OCR quick entry navigates to `/ocr`.
- Unimplemented quick entries do not pretend to be functional.
- No backend, database, Docker, provider, or credit logic is changed.
- UI remains usable at `1280px` width.

## Test Method

Run from `D:\Project\ad-assistant\desktop-app`:

```powershell
npm run build
```

Run from `D:\Project\ad-assistant`:

```powershell
git diff --check
```

If a local dev preview is needed, use the native local frontend toolchain. Do not introduce Docker for this task.

## Dependency Policy

No new dependency is allowed by default.

If a new icon/UI dependency is proposed, CC must stop and explain:

- dependency name,
- why existing Vue/CSS cannot solve it,
- bundle and maintenance risk,
- exact files to change.

User approval is required before adding it.

## Major Change Status

Major change: No.

Reason:

- This is a frontend UI shell and routing update.
- No backend behavior changes.
- No data migration.
- No real billing or provider behavior changes.

Rollback plan:

- Revert the dashboard UI files and restore `/` routing to the prior behavior.

## Security Checks

- Do not expose API keys in the client.
- Do not implement client-side credit deduction.
- Do not bypass cloud authorization.
- Do not store new tokens.
- Do not log sensitive auth data.
- Do not present mock server status as verified real connectivity.

## Completion Output Required

CC must report:

- changed file list,
- implementation summary,
- unimplemented or placeholder behavior,
- exact test commands and results,
- whether any dependency was added,
- whether any forbidden area was touched,
- screenshots or a concise visual summary if available.
