# S05-R07: 代码签名准备与签名集成方案

## 背景

S04-T08 完成 Tauri 打包 Smoke 验证（EXE/MSI/NSIS 生成成功），S04 E2E Smoke 确认所有打包产物未签名，Windows SmartScreen 显示 "Windows protected your PC" 警告。S05-R06 完毕后，在真实支付前应先建立签名方案。

S05-R07 仅建立方案文档，不产生签名产物、不修改 CI 配置、不提交凭据。

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `docs/29-code-signing-plan.md` | **NEW** — 代码签名方案全文 |
| `docs/17-release-and-update.md` | 补充代码签名检查项和方案链接 |
| `docs/module-context/sprint-05-risk-07-code-signing-plan/context.md` | **NEW** — 本文件 |
| `PROGRESS.md` | 进度记录 |
| `tasks/current-task.md` | 状态更新 |

### 未修改

- 无代码变更
- 无 `tauri.conf.json` 修改
- 无 CI 配置变更
- 无新增依赖

## 方案要点

### 证书类型推荐

- 内测 v0.1.x：不签名（当前状态）
- 付费试点 v0.2.x：OV Code Signing（DigiCert/Sectigo）— $200–400/年
- 正式商业 v1.0.x：EV Code Signing（DigiCert）— $300–600/年

### 私钥保护

- 推荐 Azure Key Vault + Managed Identity
- 备选加密 PFX + CI secrets
- 禁止裸 PFX 提交到仓库

### Tauri 集成

- 通过 `bundle.windows.signCommand` 配置
- 通过环境变量注入证书路径/密码
- 签名后验证作为构建步骤

## 安全

- 本文档不包含任何真实证书、私钥、密码或 token
- 所有路径和密码均为 PLACEHOLDER 占位符
- 实际签名实现由后续任务在用户提供证书后执行
- `.github/**` 和 `desktop-app/src-tauri/**` 未修改

## 残余风险

- SmartScreen 信誉累积需数周至数月（OV 证书）
- 证书申请需要企业营业执照（前置依赖未确认）
- 未接入 CI 签名流程（仅方案，未实现）
- 未实现自动签名验证 CI 步骤
