# 当前任务：Sprint-01 Task-06 收尾交接与文档同步

## 状态

`MVP_REQUIRED` - 由 CC 实现文档/任务收尾，Codex Review。

## 建议分支

`docs/sprint-01-task-06-handoff`，基于 `main` 当前最新提交。

## 前置任务

- Task-01 项目骨架搭建：已完成
- Task-02 Auth/Device 方案设计：已完成
- Task-03 Auth/Device 实现：已完成，已合并到 main
- Task-04 OCR 最小闭环：已完成，已合并到 main
- Task-05 使用统计基础表 + provider_call_log 表：已完成，已合并到 main
- Task-05 小修：`estimated_cost=0` 序列化不应返回 `null`，已合并到 main

## 背景

Sprint-01 已经完成认证设备、OCR 最小闭环、OCR 历史、usage_events 和 provider_call_log 基础能力。进入下一个业务模块前，需要先完成 Sprint-01 收尾交接：

1. 把当前 `main` 的完成状态写清楚。
2. 同步 API 文档与 Task-05 实现之间的已知差异。
3. 记录 Task-05 的残余风险和测试结果。
4. 明确下一阶段候选任务，但不启动新业务开发。

本任务只做文档和任务交接，不写业务代码。

## 本次只开发什么

### 1. 更新 API 文档

更新 `docs/05-api-contract.md` 中 Usage API 和 Provider Log API 的描述，使其与 Task-05 当前实现一致：

- `GET /api/v1/usage/events`
  - 需要鉴权。
  - 普通用户只能查询自己的 usage_events。
  - 支持 `limit`、`offset`、`feature`。
  - 返回统一结构 `{success, data, error, request_id}`。

- `GET /api/v1/provider-call-logs`
  - 需要鉴权。
  - 普通用户只能查询自己的 provider_call_log。
  - 支持 `limit`、`offset`、`feature`、`status`。
  - 返回统一结构 `{success, data, error, request_id}`。
  - 不返回 prompt 原文、图片原文、API Key、Token、完整隐私内容。

说明：如果文档仍保留“仅后台管理员或授权用户可访问”的表达，需要改为“当前 Sprint-01 允许普通用户查询自己的日志；后台管理查询另行任务实现”。

### 2. 新增或更新 Sprint-01 收尾摘要

建议新增：

- `docs/sprint-01-summary.md`

内容至少包括：

- Sprint-01 已完成模块列表。
- 每个模块对应的主分支合并提交。
- 当前云端 API 能力。
- 当前本地 OCR 能力。
- 当前数据库/本地 SQLite 表。
- 已知残余风险。
- 下一阶段候选任务建议。

### 3. 记录 Task-05 残余风险

在 `docs/sprint-01-summary.md` 或现有合适文档中记录：

- Task-05 后端测试通过：`pytest tests/ -v` 曾验证为 `79 passed`。
- Task-05 只做 SQLite ORM 测试 + DDL 静态检查，没有真实 PostgreSQL migration integration test。
- DDL rollback 当前是注释形式的 `DROP TABLE`，后续迁移体系需要正规化。
- provider_call_log 当前是基础表和最小查询，不代表真实 AI Provider 已接入。
- credit deduction / credit_ledger 真实扣费尚未实现。

### 4. 整理下一阶段候选任务

在 `docs/sprint-01-summary.md` 中列出候选，不实现：

- 候选 A：Sprint-02 Task-01 AI 算力账户与 credit_ledger 基础表。
- 候选 B：Sprint-02 Task-01 云端 Provider 抽象与模拟 Provider 调用。
- 候选 C：Sprint-02 Task-01 PostgreSQL migration/integration test 基础设施。

候选任务只写建议，不创建业务代码，不创建 Provider 实现，不创建扣费逻辑。

### 5. 更新任务状态

可继续维护本文件 `tasks/current-task.md`，使其表示当前 Task-06 收尾任务。

## 本次不开发什么

- 不修改 cloud-backend 业务代码。
- 不新增或修改数据库表结构。
- 不新增 migration DDL。
- 不实现 `credit_accounts`。
- 不实现 `credit_ledger`。
- 不实现真实扣费。
- 不实现会员、套餐、支付、充值、赠送额度。
- 不实现真实 AI Provider 调用。
- 不修改 `cloud-backend/app/providers/`。
- 不修改 Auth/Device 核心逻辑。
- 不修改 Token 逻辑。
- 不修改 Tauri 权限。
- 不修改 desktop-app 业务代码。
- 不新增前端页面。
- 不引入新依赖。
- 不实现后台管理系统。
- 不实现 BACKLOG / FUTURE 功能。

## 允许修改哪些文件

仅允许修改：

- `tasks/current-task.md`
- `docs/05-api-contract.md`
- `docs/13-module-roadmap.md`（仅用于状态备注，不能扩展 Sprint-01 功能范围）
- `docs/sprint-01-summary.md`（新文件）

如果需要修改其他文档，必须先说明原因并等待用户确认。

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `cloud-backend/app/**`
- `cloud-backend/tests/**`
- `cloud-backend/migrations/**`
- `desktop-app/**`
- `shared/**`
- `official-website/**`
- `tools/**`
- `.github/**`
- 任何依赖配置文件
- 任何锁文件

## 验收标准

- `docs/05-api-contract.md` 与 Task-05 当前 API 行为一致。
- `docs/sprint-01-summary.md` 清楚记录 Sprint-01 已完成内容、测试结果、残余风险和下一阶段候选任务。
- 文档没有声称尚未实现的能力。
- 文档没有把候选任务写成已完成任务。
- 文档没有扩大 Sprint-01 允许开发范围。
- 没有修改业务代码、数据库迁移、Provider、Auth/Device、Tauri、前端代码。
- `git diff --check` 通过。

## 测试方式

本任务是文档收尾任务，必须执行：

```powershell
git status --short --branch
git diff --check
```

如果没有修改业务代码，不要求运行后端 pytest。若执行者误改业务代码，必须停止并等待 Codex Review。

## 是否允许新增依赖

否。

## 是否涉及重大变更

否。

本任务只修改文档和任务交接内容，不修改数据库 schema、API 实现、Provider 接口、Auth/Token、扣费、支付、Tauri 权限或本地服务启动方式。

## 安全检查

- 不下发 API Key 到客户端。
- 不由客户端扣点。
- 不由客户端决定套餐、权限或是否免费。
- 不绕过云端授权。
- 不保存明文 Token。
- 不新增 AI Provider 调用。
- 不新增远程命令执行能力。
- 不放宽文件系统权限。

## 给 Codex Review 的审查指引

请审查 Sprint-01 Task-06 收尾交接与文档同步任务。

重点检查：

1. 是否只修改允许的文档文件。
2. 是否没有业务代码、数据库、Provider、Auth/Token、Tauri、前端变更。
3. `docs/05-api-contract.md` 是否与 Task-05 当前实现一致。
4. `docs/sprint-01-summary.md` 是否准确记录已完成内容和残余风险。
5. 是否没有把未实现的 credit、Provider、支付、后台能力描述成已完成。
6. 是否没有扩大 Sprint-01 范围。
7. 是否通过 `git diff --check`。

输出：

- 任务单结构完整性
- 范围越界检查
- 文档准确性检查
- 安全风险检查
- 是否允许提交

## 完成输出要求

执行者完成后必须输出：

- 修改文件列表
- 实现内容
- 未实现内容
- 测试命令和结果
- 风险点
- 是否触发重大变更
- 等待 Codex Review，不得自行提交
