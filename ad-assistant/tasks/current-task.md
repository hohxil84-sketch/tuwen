# S05-R07: 代码签名准备与签名集成方案

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-07-code-signing-plan`

## 背景

当前 EXE/MSI/NSIS 未签名，Windows SmartScreen 会提示风险。代码签名需要证书、私钥、安全存储和发布流程，是高风险发布链路任务。

先建立可执行的代码签名方案和本地/CI 集成边界，明确证书准备、私钥保护、签名命令、验证方式和未签名 fallback。

## 用户目标

建立可执行的代码签名方案文档，明确证书类型、获取途径、私钥存储策略、签名命令模板、验证步骤、SmartScreen 风险说明，为后续真实签名实现提供决策依据。

## What To Build

1. **代码签名方案文档** (`docs/29-code-signing-plan.md`)
   - 证书类型对比（EV / OV / 自签名 / Let's Encrypt 不适用原因）
   - 推荐获取途径和预估成本
   - 私钥保护策略（HSM / Azure Key Vault / 本地加密 PFX）
   - Tauri bundle 签名配置模板
   - 签名命令模板（signtool + PFX、CI 环境变量注入）
   - 签名验证命令和步骤
   - 未签名 fallback 与 SmartScreen 风险说明
   - 时间戳服务配置

2. **更新发布文档** (`docs/17-release-and-update.md`)
   - 补充代码签名检查项
   - 链接到详细方案文档

3. **模块上下文** (`docs/module-context/sprint-05-risk-07-code-signing-plan/context.md`)

## What Not To Build

- 不生成或购买真实证书
- 不提交证书、私钥、密码或 PFX
- 不改 CI secrets（`.github/**`）
- 不修改 Tauri 配置或 Rust 源码
- 不正式发布安装包

## Allowed Files

- `docs/17-release-and-update.md`
- `docs/29-code-signing-plan.md`
- `docs/module-context/sprint-05-risk-07-code-signing-plan/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- `.github/**`
- `desktop-app/src-tauri/**`
- 任何证书、私钥、PFX、密码、生产发布凭据
- CI/deployment 配置

## Acceptance Criteria

- [ ] 文档说明证书类型、获取途径、预估成本
- [ ] 明确私钥存储策略和安全要求
- [ ] 包含签名命令模板和验证命令
- [ ] 包含 Tauri bundle 签名配置建议
- [ ] 明确当前未签名风险仍存在
- [ ] 不提交任何敏感凭据
- [ ] `git diff --check` 通过

## Test Method

```bash
git diff --check
```

人工审查：文档不含 secrets、路径均为占位符。

## Dependency Permission

不允许新增依赖。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及发布链路和签名凭据安全。

## Security Requirements

- 绝不提交证书、私钥、密码或 token
- 文档只能写占位路径和示例命令
- 不记录真实凭据到任何项目文件

## Rollback Plan

- revert 文档 commit

## Completion Output Required

- 签名方案摘要
- 未实现内容
- 凭据安全说明
- 风险
- 回滚方式
- 中文 commit message
- PR 摘要
