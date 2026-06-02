# S05-R01: 余额不足 402 桌面端充值引导

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-01-insufficient-balance-ux`

## 完成摘要

- `cloudApi.ts`：`CloudAPIErrorDetail` 新增 `request_id?` 字段；`request()` 抛错时附加 `body.request_id`；`sanitizeApiError` codeMap 新增 `INSUFFICIENT_BALANCE`
- `AdCopyPage.vue`：检测 `INSUFFICIENT_BALANCE` → 展示中文错误消息 + "去充值 →"按钮（跳转 `/membership`）+ request_id（小字等宽）；非 402 错误保持原有纯文本展示
- 模块上下文 `docs/module-context/sprint-05-risk-01-insufficient-balance-ux/context.md` 已创建
- `docs/09-desktop-app-guide.md` 已补充 402 UX 说明
- `npm run build`：74 modules, 0 errors（含 vue-tsc 类型检查）
- `git diff --check`：通过
- `PROGRESS.md` 已追加记录

## 背景

S04-T01 已实现 Provider 调用前余额检查，余额不足时后端返回 402 + `INSUFFICIENT_BALANCE` 错误码 + 中文提示。当前桌面端 `sanitizeApiError` 的 `codeMap` 缺少 `INSUFFICIENT_BALANCE` 映射，且 AI 文案页面只有纯文本错误提示，没有"去充值"入口和 `request_id` 展示。用户看到错误后不知道如何恢复。

后端 402 响应格式（已有）：
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "积分余额不足，当前余额 0 积分，至少需要 100 积分...",
    "details": { "balance": 0, "required": 100 }
  },
  "request_id": "req_xxx"
}
```

当前代码路径：
1. `cloudApi.ts` `request()` → 检测 `!response.ok || !body.success` → 抛出 `body.error`（`{code, message, details}`），**丢失 `request_id` 和 HTTP status**
2. `authStore.ts` `callMockAdCopy()` → 透传异常
3. `AdCopyPage.vue` `handleSubmit()` → `catch` 中调用 `sanitizeApiError(apiErr)` → 仅得到中文字符串 → 纯文本展示

## 用户目标

当用户因余额不足（402 / `INSUFFICIENT_BALANCE`）无法生成 AI 文案时，桌面端能：
- 清晰提示余额不足原因
- 提供"去充值"按钮一键跳转会员中心
- 保留 `request_id` 便于排查

## What To Build

### 1. `cloudApi.ts` — 错误对象补全（必要联动）

- `CloudAPIErrorDetail` 新增可选字段 `request_id?: string`
- `request()` 函数在抛出错误时，将 `body.request_id` 附加到错误对象上，使调用方可追溯
- `sanitizeApiError` 的 `codeMap` 新增：
  ```
  INSUFFICIENT_BALANCE: "积分余额不足，请充值后再试。"
  ```
- 不修改 `request()` 的成功路径和已有错误分支行为

### 2. `AdCopyPage.vue` — 402 差异化 UX

- 新增 `insufficientBalance` 响应式状态（`ref<boolean>(false)`）
- 新增 `errorRequestId` 响应式状态（`ref<string | null>(null)`）
- 在 `handleSubmit` 的 `catch` 块中：
  - 检查 `apiErr.code === "INSUFFICIENT_BALANCE"`
  - 若是，设置 `insufficientBalance = true` + `errorRequestId = apiErr.request_id`
  - 若否，`insufficientBalance = false`
  - 错误消息仍通过 `sanitizeApiError` 获取
- 模板中当 `insufficientBalance` 为 `true` 时：
  - 在错误提示区域展示：
    - 错误消息（现有 `.error-msg` 样式）
    - "去充值" 按钮 → 调用 `router.push("/membership")`
    - `request_id` 展示（小字、等宽字体、可选复制）
  - 非 402 错误保持现有纯文本错误展示逻辑不变
- 提交成功后（生成文案成功不再显示 402）重置 `insufficientBalance` 和 `errorRequestId`

### 3. 文档

- 更新 `docs/09-desktop-app-guide.md`：补充 402/余额不足 UX 说明
- 新增 `docs/module-context/sprint-05-risk-01-insufficient-balance-ux/context.md`

### 4. 进度记录

- 追加更新 `PROGRESS.md`
- 更新 `tasks/current-task.md` 完成后状态

## What Not To Build

- 不修改后端扣费、余额检查、Provider 路由或套餐规则
- 不接入真实支付
- 不新增 API contract 或 shared DTO
- 不修改 `cloudApi.ts` 的请求/响应核心逻辑（仅扩展错误对象）
- 不新增依赖
- 不在其他页面（OcrPage 等）添加类似 402 处理（范围仅 AdCopyPage）
- 不修改 `authStore.ts`

## Allowed Files

- `desktop-app/src/pages/AdCopyPage.vue`
- `desktop-app/src/services/cloudApi.ts`（仅错误对象补全，不改变请求/响应核心逻辑）
- `docs/09-desktop-app-guide.md`
- `docs/module-context/sprint-05-risk-01-insufficient-balance-ux/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`（完成后仅允许状态、分支、简短完成摘要、commit/PR 信息）

## Forbidden Files

- `cloud-backend/**`
- `desktop-app/src-tauri/**`
- `desktop-app/src/stores/**`
- `desktop-app/src/components/**`
- `desktop-app/src/pages/`（除 AdCopyPage.vue 外）
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `shared/**`
- `official-website/**`
- `.github/**`
- 数据库 DDL / migrations
- Provider、Credit、Payment、Billing 相关代码

## Dependency Permission

不允许新增依赖。

## Major Change Status

`NO_MAJOR_CHANGE_EXPECTED`

原因：仅修改桌面端错误展示和入口引导，不改变后端逻辑、API contract、Provider 路由、扣费算法或 Tauri 权限。

必须暂停确认的情况：
- 需要修改后端、shared、数据库、Provider、Credit、Payment 或 Tauri 权限
- 需要新增 API 端点或修改 API contract
- 需要在 AdCopyPage.vue 和 cloudApi.ts 之外修改文件
- 需要新增依赖

## Security Requirements

- 不绕过后端授权、余额检查或扣费逻辑
- 不在客户端决定套餐、余额或扣费结果
- 不修改 token 存储策略
- 不提交 `dist/**`、构建产物或日志

## Acceptance Criteria

- [ ] 余额不足时 AI 文案页面显示中文提示 + "去充值"按钮 + request_id
- [ ] 点击"去充值"按钮跳转到 `/membership` 会员中心页面
- [ ] 非 402 错误（网络超时、未登录、服务异常等）仍按原有纯文本错误逻辑显示
- [ ] 成功生成文案后，之前的 402 状态和 request_id 自动清除
- [ ] `CloudAPIErrorDetail` 新增 `request_id?` 字段，错误路径不丢失 request_id
- [ ] `sanitizeApiError` 的 `codeMap` 包含 `INSUFFICIENT_BALANCE`
- [ ] 不修改后端、shared、数据库、Tauri 权限、依赖或 CI
- [ ] `npm run build` 通过
- [ ] `git diff --check` 通过
- [ ] `PROGRESS.md` 已追加本任务记录

## Test Method

必须运行：

```powershell
cd ad-assistant/desktop-app
npm run build
```

```powershell
git diff --check
```

必须检查：

```powershell
git status --short --branch
```

建议手动验证（需运行后端 + 低余额测试用户）：

1. 用余额不足的测试用户登录
2. 进入 AI 文案生成页面，提交表单
3. 验证：显示余额不足提示 + "去充值"按钮 + request_id
4. 点击"去充值" → 验证跳转到 `/membership`
5. 用正常余额用户提交 → 验证正常生成文案

如果后端/本地服务不可用，至少完成 `npm run build` + `git diff --check` + 静态代码审查。

## Rollback Plan

- revert 本任务 commit，恢复 AI 文案页面纯文本错误逻辑
- 不影响后端、数据库、API contract 或用户数据

## Completion Output Required

执行者完成后必须用中文输出：

- 修改文件列表
- UX 行为变更说明
- 测试命令和结果
- 未实现内容
- 自审结论
- reviewer-mode 自查结论
- 是否触发高风险暂停规则
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 风险和回滚方式
- 中文 commit message
- PR title/body 中文摘要
