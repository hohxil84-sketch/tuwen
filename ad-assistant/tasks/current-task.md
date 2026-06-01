# Current Task: Sprint-02 Task-08 Mock AI API Contract Formalization

## Status

`IMPLEMENTED_SELF_REVIEW_PASSED`

Implemented by Claude Code on 2026-06-01. Self-review passed. Awaiting commit + push + PR.

## Implementation Evidence

- **Branch**: `feature/sprint-02-task-08-mock-ai-api-contract`
- **Backend**: `APIResponse[T]` generic model wired on `POST /api/v1/mock-ai/ad-copy`
- **Shared OpenAPI**: `shared/openapi/mock-ai.yaml` — first real spec
- **Shared DTO**: `shared/dto/mock-ai.ts` — first real TypeScript DTO
- **Tests**: 147 SQLite regression ✅, 21 mock AI focused ✅
- **OpenAPI gen**: `MockAdCopyData` + `APIResponse_MockAdCopyData_` in schemas ✅
- **git diff --check**: ✅
- **Wire response unchanged**: ✅

## Background

The mock AI endpoint `POST /api/v1/mock-ai/ad-copy` is implemented and working (Task-04 + Task-05), but the API contract exists only as Pydantic schemas inside the backend. The project's `shared/openapi/` and `shared/dto/` directories are empty skeletons from Sprint-01.

Per `docs/05-api-contract.md`: "API 契约必须稳定、可版本化、可生成类型。所有前后端交互以 `shared/openapi/` 为准。"

Current gaps:

| Gap | Detail |
|-----|--------|
| `response_model=None` | All endpoints (including mock-ai) use `response_model=None`. FastAPI cannot generate correct OpenAPI docs or validate responses at runtime. |
| `shared/openapi/` empty | No OpenAPI YAML specs exist — `.gitkeep` only |
| `shared/dto/` empty | No TypeScript DTOs exist — `.gitkeep` only |
| Generic response wrapper not wired | `APIResponse[MockAdCopyData]` is not used as a FastAPI generic response model |

The desktop mock AI client (Task-05) depends on the response shape but has no machine-readable contract to validate against. Future endpoints will face the same problem.

## Goal

Create the first end-to-end API contract pipeline for the mock AI endpoint:

1. Backend: wire a generic `response_model` so FastAPI validates responses at runtime and auto-generates correct OpenAPI
2. Shared: create `shared/openapi/mock-ai.yaml` — the first real OpenAPI spec
3. Shared: create `shared/dto/mock-ai.ts` — the first shared TypeScript DTO

This establishes the pattern for all future endpoints.

## What To Build

### 1. Generic response model (backend)

Add `APIResponse[T]` as a generic Pydantic model so `response_model` can be wired on endpoints with typed `data`:

```python
# app/schemas/common.py — new generic wrapper
from typing import Generic, TypeVar
T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    request_id: str | None = None
```

### 2. Wire `response_model` on mock AI endpoint (backend)

Update `POST /api/v1/mock-ai/ad-copy`:

```python
@router.post(
    "/mock-ai/ad-copy",
    response_model=APIResponse[MockAdCopyData],  # was: response_model=None
    status_code=status.HTTP_200_OK,
)
```

And return `APIResponse[MockAdCopyData]` directly. The `success_response()` helper should accept Pydantic model instances (not just dicts) so it can construct `APIResponse(data=mock_ad_copy_data)` without `.model_dump()` first. FastAPI serializes the model via `response_model`.

### 3. Create `shared/openapi/mock-ai.yaml`

First real OpenAPI spec. Include:
- Unified response wrapper schema
- `POST /api/v1/mock-ai/ad-copy` request/response definition
- `MockAdCopyData` response schema
- Error response examples (401, 403)

### 4. Create `shared/dto/mock-ai.ts`

TypeScript types mirroring the OpenAPI spec:
- `MockAdCopyRequest`
- `MockAdCopyData`
- `APIResponse<T>`
- `ErrorDetail`

### 5. Documentation updates

- `docs/23-mock-ai-api-endpoint.md` — add OpenAPI/DTO file references
- `docs/05-api-contract.md` — note first spec created
- `docs/sprint-02-summary.md` — add Task-08 status
- `shared/openapi/.gitkeep` — update to reflect first spec created
- `shared/dto/.gitkeep` — update to reflect first DTO created

## What Not To Build

- Do NOT create OpenAPI specs for auth, device, credit, or other endpoints — mock-ai only
- Do NOT create DTOs for other endpoints
- Do NOT change API behavior, request/response shapes, or business logic
- Do NOT touch provider layer, auth chain, credit/payment
- Do NOT modify `shared/error-codes/` (separate task)
- Do NOT add API versioning or API gateway changes
- Do NOT add new dependencies
- Do NOT add new tests (existing 147 + 21 must continue to pass)

## Allowed Files

- `cloud-backend/app/schemas/common.py` — add generic `APIResponse[T]`
- `cloud-backend/app/api/v1/mock_ai.py` — wire `response_model`
- `cloud-backend/app/schemas/mock_ai.py` — minor adapt if needed
- `shared/openapi/mock-ai.yaml` — new OpenAPI spec
- `shared/openapi/.gitkeep` — update or remove
- `shared/dto/mock-ai.ts` — new TypeScript DTO
- `shared/dto/.gitkeep` — update or remove
- `docs/23-mock-ai-api-endpoint.md` — add references
- `docs/05-api-contract.md` — minor update
- `docs/sprint-02-summary.md` — add Task-08
- `tasks/current-task.md` — this file
- `PROGRESS.md` — add entry

## Forbidden Files

- `cloud-backend/app/api/v1/auth.py`, `device.py` — other endpoints
- `cloud-backend/app/services/**` — service code
- `cloud-backend/app/providers/**` — provider code
- `cloud-backend/app/core/**` — core code
- `cloud-backend/app/models/**` — model code
- `cloud-backend/tests/**` — test files
- `shared/error-codes/**`
- `shared/sdk/**`, `shared/typescript/**`, `shared/constants/**`
- `desktop-app/**` — desktop code
- `official-website/**` — website code
- `migrations/**`
- `.github/workflows/**`
- dependency files (`pyproject.toml`, `package.json`, lockfiles)
- `.env` files

## Acceptance Criteria

1. `APIResponse[T]` generic model exists in `app/schemas/common.py` and is compatible with existing `success_response()` / `error_response()` helpers
2. `POST /api/v1/mock-ai/ad-copy` uses `response_model=APIResponse[MockAdCopyData]`
3. FastAPI `/docs` (Swagger UI) shows the correct response schema for the mock AI endpoint
4. FastAPI `/openapi.json` includes the `MockAdCopyData` schema in `components/schemas`
5. `shared/openapi/mock-ai.yaml` exists with complete request/response definitions
6. `shared/dto/mock-ai.ts` exists with TypeScript types matching the spec
7. Existing 147 SQLite tests + 21 mock AI tests all pass (regression)
8. `git diff --check` passes

## Test Method

### Regression tests (must pass)

```bash
cd d:/Project/ad-assistant/cloud-backend
python -m pytest tests/ -v --ignore=tests/test_migrations_integration.py
# Expected: 147 passed
```

### mock AI focused tests (must pass)

```bash
cd d:/Project/ad-assistant/cloud-backend
python -m pytest tests/test_mock_ai_api.py -v
# Expected: 21 passed
```

### FastAPI OpenAPI generation verification

```bash
cd d:/Project/ad-assistant/cloud-backend
python -c "
from app.main import app
spec = app.openapi()
schemas = spec.get('components', {}).get('schemas', {})
assert 'MockAdCopyData' in schemas, f'MockAdCopyData not found: {list(schemas.keys())}'
assert 'APIResponse_MockAdCopyData_' in schemas or any(k.startswith('APIResponse') for k in schemas), f'APIResponse generic not found'
paths = spec.get('paths', {})
assert '/api/v1/mock-ai/ad-copy' in paths, 'mock-ai path not found'
print('OK: FastAPI OpenAPI includes MockAdCopyData + APIResponse + mock-ai path')
"
```

## Dependency Permission

No new dependencies.

## Major Change Status

**是 — 重大变更。** 原因：
- 修改 API response schema 绑定 → 影响 OpenAPI 生成
- 创建 `shared/openapi/` 和 `shared/dto/` 下的第一个正式文件 → 共享契约变更
- 属于 CODEX.md 中定义的"API contract / OpenAPI / shared DTO"高风险边界

### What this actually changes

| Layer | Change |
|-------|--------|
| API behavior | **None** — same HTTP response body |
| FastAPI metadata | **Yes** — `response_model` now bound, OpenAPI JSON now complete |
| `shared/` contracts | **Yes** — first real OpenAPI spec and TypeScript DTO |
| Runtime validation | **Yes** — FastAPI validates response against schema before returning |

Backward compatibility: wire response is identical — desktop mock client needs zero changes.

## Security Requirements

- Do NOT expose `raw_usage` in response schema or OpenAPI spec
- Do NOT include `user_id`, `device_id`, or internal identifiers in response DTO
- Do NOT add real AI provider credentials or endpoints
- Do NOT change authentication or authorization logic
- Keep `credits_charged=0` and mock-only behavior intact

## Rollback Plan

1. Revert `app/api/v1/mock_ai.py` — restore `response_model=None`
2. Revert `app/schemas/common.py` — remove generic `APIResponse[T]`, restore original
3. Remove `shared/openapi/mock-ai.yaml` and `shared/dto/mock-ai.ts`
4. Restore `.gitkeep` files in shared directories
5. No DB rollback needed

## Suggested Branch

`feature/sprint-02-task-08-mock-ai-api-contract`

## Completion Output Required

- Changed files (with diff stat)
- Exact test commands and results
- OpenAPI generation verification output
- Confirmation that wire response is unchanged
- Confirmation that no other endpoints, provider, auth, credit, or dependency changes were made
- Residual risks
- Module context updated
- Commit and PR created (self-review passed)
