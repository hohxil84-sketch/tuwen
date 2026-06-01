# 项目进度

本文件用于记录 AI 图文广告助手项目的模块级进度。

Claude Code / DeepSeek 每完成一个模块或任务后，必须追加一条记录。记录要基于事实，保持简洁；不得写入真实密钥、Token、生产数据库连接串或用户隐私数据。

## 记录模板

```markdown
## YYYY-MM-DD - <模块或任务名称>

状态：<PLANNED | IN_PROGRESS | IMPLEMENTED_SELF_REVIEW_PASSED | IMPLEMENTED_NEEDS_FIX | BLOCKED | MERGED>

分支：
提交：
PR：

### 范围

- 目标：
- 已实现：
- 未实现：

### 主要改动

- <文件或模块>：<说明>

### 自检结果

- 任务单完整：
- 修改范围符合 allowed files：
- 未触碰未确认高风险变更：
- 未加入密钥或生产凭据：
- 模块上下文已更新：
- Bug 根因已记录（如适用）：

### 测试结果

- <命令>：<结果>

### 风险和后续

- 残余风险：
- 后续任务：
- 回滚方式：
```

## 记录

## 2026-06-01 - Agent Workflow CC Autonomous Handoff

状态：MERGED

分支：`docs/cc-autonomous-workflow`
提交：`33cc6a9`
PR：#21（已合并到 `main` @ `fe5e94f`）

### 范围

- 目标：将项目流程调整为 CC 自主写任务单、实现、测试、自审、提交任务分支、push 和准备 PR。
- 已实现：项目协作规则、Git 守卫规则、`PROGRESS.md` 进度账本、Bug 根因优先流程、本地 task executor / git guardrails skill 同步更新。
- 未实现：未开发业务功能；未修改 backend、desktop、API/schema/provider/auth/credit/Tauri/CI/dependency。

### 主要改动

- `CLAUDE.md`：定义 CC 自主执行、任务单生成、自审、Bug 修复和进度记录规则。
- `CODEX.md`：将 Codex 改为按需复核，不再作为默认强制门禁。
- `README.md`：更新开发流程和 `PROGRESS.md` 记录要求。
- `docs/14-ai-agent-workflow.md`：记录 CC 自主协作流程和 Bug 修复流程。
- `docs/16-git-workflow.md`：允许 CC 自审通过后提交和 push 任务分支，同时保留 `main` 只能 PR 合并。
- `docs/20-agent-git-guardrails.md`：将默认门禁改为 CC 自审，并要求更新 `PROGRESS.md`。
- `PROGRESS.md`：新增项目进度账本和记录模板。
- `tasks/current-task.md`：记录本次 workflow 调整任务。
- 本地 skills：更新 `ad-assistant-task-executor` 和 `ad-assistant-git-guardrails`。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（workflow-only 规则变更）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- `git diff --check`：通过
- `quick_validate.py ad-assistant-task-executor`：通过
- `quick_validate.py ad-assistant-git-guardrails`：通过
- PR #21 `pg-integration`：通过

### 风险和后续

- 残余风险：CC 自主权更高；主要控制点是 `main` PR-only、不 self-merge、高风险暂停规则和必要时按需复核。
- 后续任务：后续产品任务按新的 CC-first 流程启动。
- 回滚方式：revert workflow 文档提交，并按需恢复本地 skill 旧版本。

## 2026-06-01 - Sprint-02 Task-07 Backend PostgreSQL DateTime Alignment

状态：MERGED

分支：`feature/sprint-02-task-07-pg-datetime-align`
提交：`80e41a1`
PR：#20（已合并到 `main` @ `1a3602f`）

### 范围

- 目标：让 SQLAlchemy models 的 `DateTime(timezone=True)` 与 DDL 的 `TIMESTAMPTZ` 对齐。
- 已实现：8 个 model 文件共 18 个 DateTime 列改为 `DateTime(timezone=True)`；更新 seed 脚本文档说明；更新相关文档。
- 未实现：未修改 DDL、API、service、provider、shared、desktop、dependency、CI 或 `.env`；未做 services/api datetime 使用全量审计。

### 主要改动

- `cloud-backend/app/models/user.py`：`DateTime(timezone=True)` 2 处。
- `cloud-backend/app/models/device.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/auth_session.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/credit_account.py`：`DateTime(timezone=True)` 4 处。
- `cloud-backend/app/models/credit_ledger.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/provider_call_log.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/risk_log.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/app/models/usage_event.py`：`DateTime(timezone=True)` 1 处。
- `cloud-backend/scripts/dev_seed_user.py`：更新 docstring。
- `docs/25-desktop-mock-e2e-smoke.md`：移除 PostgreSQL 绕过说明。
- `docs/11-cloud-backend-guide.md`：更新 PostgreSQL 支持状态。
- `docs/12-database-design.md`：新增 timestamp 对齐说明。
- `docs/sprint-02-summary.md`：新增 Task-07 状态块。
- `docs/module-context/sprint-02-task-07-pg-datetime-align/context.md`：新增模块上下文。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：是
- Bug 根因已记录（如适用）：是，根因为 ORM/DDL DateTime 类型不匹配

### 测试结果

- SQLite regression：147 passed
- PG DDL integration：55 passed
- ORM `create_all` against PG：succeeded
- `dev_seed_user.py` against PG：user created + device bound
- `git diff --check`：通过

### 风险和后续

- 残余风险：services/api 代码中可能仍有 datetime naive 假设，后续需要专项审查。
- 后续任务：Task-08（API response / OpenAPI / shared DTO）。
- 回滚方式：revert 对应提交，恢复 model 文件中未声明 `DateTime(timezone=True)` 的状态。

## 2026-06-01 - Sprint-02 Task-08 Mock AI API Contract Formalization

状态：IMPLEMENTED_SELF_REVIEW_PASSED

分支：`feature/sprint-02-task-08-mock-ai-api-contract`
提交：（待提交）
PR：（待创建）

### 范围

- 目标：为 mock AI endpoint 建立第一个端到端 API 契约管道 — generic `APIResponse[T]`、`response_model` 绑定、OpenAPI spec、TypeScript DTO。
- 已实现：`APIResponse[T]` generic model、mock-ai 端点绑定 `response_model=APIResponse[MockAdCopyData]`、`shared/openapi/mock-ai.yaml`、`shared/dto/mock-ai.ts`。
- 未实现：不涉及其他端点、不涉及 provider/auth/credit 变更、不新增测试、不新增依赖。

### 主要改动

- `cloud-backend/app/schemas/common.py`：增加 `Generic`/`TypeVar` import，`APIResponse` 改为 `APIResponse(BaseModel, Generic[T])`，helper 函数返回 `APIResponse[Any]`。
- `cloud-backend/app/api/v1/mock_ai.py`：import `APIResponse`，`response_model=None` → `response_model=APIResponse[MockAdCopyData]`，`response_data.model_dump()` → 直接传 Pydantic model 实例。
- `shared/openapi/mock-ai.yaml`：新建 OpenAPI 3.0.3 spec（完整 path、request/response schema、error 示例）。
- `shared/dto/mock-ai.ts`：新建 TypeScript DTO（`MockAdCopyRequest`、`MockAdCopyData`、`APIResponse<T>`、`ErrorDetail`）。
- `shared/openapi/.gitkeep`：更新内容，反映第一个 spec 已创建。
- `shared/dto/.gitkeep`：更新内容，反映第一个 DTO 已创建。
- `docs/23-mock-ai-api-endpoint.md`：新增 OpenAPI/DTO 参考章节 + Task-08 实现证据。
- `docs/05-api-contract.md`：补充首个 spec/DTO 说明。
- `docs/sprint-02-summary.md`：新增 Task-08 状态块，移除已合并的 Task-07 状态块，移除 Candidate B。

### 自检结果

- 任务单完整：是
- 修改范围符合 allowed files：是
- 未触碰未确认高风险变更：是（重大变更已由用户确认）
- 未加入密钥或生产凭据：是
- 模块上下文已更新：不适用（API contract 层，无独立模块上下文目录；合同本身即为权威文档）
- Bug 根因已记录（如适用）：不适用

### 测试结果

- SQLite regression：147 passed
- Mock AI focused：21 passed
- FastAPI OpenAPI 生成验证：`MockAdCopyData` 在 schemas 中，`APIResponse_MockAdCopyData_` 存在，`/api/v1/mock-ai/ad-copy` 在 paths 中
- `git diff --check`：通过
- 接口返回 shape 未变：是（wire response 完全一致）

### 风险和后续

- 残余风险：其他端点仍使用 `response_model=None`，后续按需逐个迁移。
- 后续任务：Candidate C — Real Provider routing design。
- 回滚方式：revert 对应提交，`response_model` 改回 `None`，移除 shared 新文件，恢复 `.gitkeep` 原始内容。
