# S05-R01: 余额不足 402 桌面端充值引导 — 模块上下文

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 日期

2026-06-02

## 分支

`feature/sprint-05-risk-01-insufficient-balance-ux`

## 方案说明

### 问题

S04-T01 已实现后端 402 + `INSUFFICIENT_BALANCE` 错误码，但桌面端：
1. `sanitizeApiError` codeMap 缺少 `INSUFFICIENT_BALANCE` 映射
2. `request()` 抛错时丢失 `body.request_id`
3. AI 文案页面只有纯文本错误提示，无"去充值"入口

### 方案

**最小桌面端 UX 补全**，不改后端、不新增 API、不修改错误处理核心逻辑：

1. **`cloudApi.ts`**：
   - `CloudAPIErrorDetail` 新增 `request_id?: string`
   - `request()` 在抛出错误时将 `body.request_id` 附加到错误对象
   - `sanitizeApiError` codeMap 新增 `INSUFFICIENT_BALANCE: "积分余额不足，请充值后再试。"`

2. **`AdCopyPage.vue`**：
   - 新增 `insufficientBalance` (boolean) 和 `errorRequestId` (string|null) 状态
   - `handleSubmit` catch 中检测 `apiErr.code === "INSUFFICIENT_BALANCE"` 设置标志
   - 模板中 `insufficientBalance` 为 true 时：错误消息 + "去充值 →"按钮 + request_id
   - 按钮点击 → `router.push("/membership")`
   - 再次提交成功或新提交时重置标志

## 修改文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `desktop-app/src/services/cloudApi.ts` | 修改 | +4 行：`request_id?` 字段 + request() 传播 + codeMap 1 行 |
| `desktop-app/src/pages/AdCopyPage.vue` | 修改 | +~30 行：2 个新状态 + goMembership() + catch 分支 + 模板条件渲染 + CSS |

### 未修改

- `desktop-app/src/stores/authStore.ts`：未修改
- `desktop-app/src/pages/` 其他页面：未修改（OcrPage 等保持原有错误处理）
- `cloud-backend/**`：未修改
- `shared/**`：未修改
- Tauri 权限、依赖、CI：未修改

## UX 行为

### 余额不足场景（402 / INSUFFICIENT_BALANCE）

```
┌─────────────────────────────────────────┐
│  积分余额不足，请充值后再试。              │
│  [去充值 →]                              │
│  request_id: req_abc123                  │
└─────────────────────────────────────────┘
```

- 错误消息使用 `sanitizeApiError` 映射的中文
- "去充值" 按钮跳转 `/membership`
- request_id 小字等宽展示，便于排查

### 非 402 错误

保持原有行为：纯文本错误消息，无按钮，无 request_id。

### 成功后重置

成功生成文案后，`insufficientBalance` 和 `errorRequestId` 在下次 `handleSubmit` 开头重置。

## 验证结果

| 测试 | 命令 | 结果 |
|------|------|------|
| 前端构建 + 类型检查 | `npm run build` | 74 modules, 0 errors ✅ |
| 空白检查 | `git diff --check` | 通过 ✅ |

## 残余风险

- **手动验证未执行**：402 差异化 UX 需后端 + 低余额用户才能真实触发。建议用户按 runbook 手动验证。
- **OcrPage 未同步处理**：OCR 页面中的 AI 文案生成功能（`OcrPage.vue` 也调用 `callMockAdCopy`）未同步添加充值引导，此处保持原有行为。
- **request_id 展示仅限 402**：非 402 错误仍不展示 request_id，保持原有用户体验。

## 回滚方式

- revert 本任务 commit，恢复 `AdCopyPage.vue` 和 `cloudApi.ts` 原有错误处理逻辑
- 不影响后端、数据库、API contract 或用户数据

## 相关文档

- [S04-T01 Provider Reliability](../../06-provider-architecture.md) — 后端 402 + INSUFFICIENT_BALANCE 实现
- [S04-T04 会员/套餐/充值](../../27-membership-recharge-rebuild-guide.md) — `/membership` 路由
- [residual-risk-tasks.md](../../../tasks/residual-risk-tasks.md) — 候选任务来源

## 自审清单

- [x] 是否只实现了 tasks/current-task.md：是
- [x] 是否任务单由用户确认：是
- [x] 是否只修改了 allowed files：是（cloudApi.ts + AdCopyPage.vue）
- [x] 是否没有混入无关文件：是
- [x] 是否没有新增未授权依赖：是
- [x] 是否没有触碰未确认的高风险边界：是
- [x] 是否没有 secrets、真实密钥、Token 或生产连接串：是
- [x] 是否完成任务单要求的测试：是（npm run build）
- [x] 是否更新模块上下文：是（本文档）
- [x] 是否列出未实现内容和残余风险：是
