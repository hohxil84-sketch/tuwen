# 29 代码签名准备与签名集成方案

## 当前状态

**当前所有 Tauri 打包产物（EXE/MSI/NSIS）均未签名。**

影响：
- Windows SmartScreen 显示 "Windows protected your PC" 警告
- 用户下载后 Microsoft Defender 可能标记为 "Unrecognized app"
- 企业用户可能被组策略阻止运行未签名应用
- 浏览器下载时标记为 "not commonly downloaded"

本文档建立可执行的签名方案，为后续真实签名实现提供决策依据。当前不包含任何真实证书、私钥或凭据。

---

## 1. 证书类型对比

### 1.1 Windows 代码签名证书类型

| 证书类型 | 颁发机构 | SmartScreen 立即信任 | 预估年费 (USD) | 组织验证 | 适用场景 |
|---------|---------|---------------------|---------------|---------|---------|
| **EV Code Signing** | DigiCert / Sectigo / GlobalSign | ✅ 是（即时） | $300–600/年 | 严格（DUNS + 营业执照 + 电话验证） | 商业发布、面向公众分发 |
| **OV Code Signing** | DigiCert / Sectigo / GlobalSign | ⚠️ 需积累信誉 | $200–400/年 | 中等（营业执照 + 电话验证） | 中小规模分发、企业内部 |
| **Standard IV** | 各 CA | ❌ 否 | $80–200/年 | 仅域名/邮箱 | 不适合 Windows 桌面应用 |
| **自签名证书** | 自己生成 | ❌ 否（红屏警告） | 免费 | 无 | 仅内部测试、CI 预发布验证 |
| **Let's Encrypt** | Let's Encrypt | ❌ 不适用 | 免费 | 仅域名 | 不支持代码签名，仅 TLS |

### 1.2 EV vs OV 关键差异

| 维度 | EV Code Signing | OV Code Signing |
|------|----------------|-----------------|
| SmartScreen 信誉 | 签署后立即建立（无警告） | 需积累下载量/时间（数周至数月） |
| 硬件要求 | **必须使用硬件 token（USB Key/FIPS 140-2 HSM）** | 可用软件 PFX 或硬件 token |
| 颁发时间 | 5–15 个工作日 | 1–5 个工作日 |
| 私钥导出 | 不可导出（硬件绑定） | 可导出为 PFX（需自行保护） |
| 时间戳 | 必须 | 强烈建议 |

### 1.3 推荐方案

**短期（内测/MVP）**：继续使用未签名产物 + 用户手动信任。（现状）

**中期（付费试点 v0.2.x）**：OV Code Signing（DigiCert 或 Sectigo）。成本可控（$200–400/年），签署后逐步积累 SmartScreen 信誉。私钥以加密 PFX 形式存储于 CI secrets。

**长期（正式商业发布 v1.0.x）**：EV Code Signing（DigiCert）。SmartScreen 即时信任，硬件 token 私钥保护，符合最高安全标准。

---

## 2. 证书获取流程

### 2.1 OV Code Signing 申请流程（以 DigiCert 为例）

1. **选择产品**：DigiCert Standard Code Signing（OV）
2. **准备材料**：
   - 企业营业执照（英文翻译件）
   - DUNS 编码（如无可由 CA 协助申请）
   - 企业电话（需能接听验证电话）
   - 签署人身份证明（护照/身份证）
3. **提交申请**：DigiCert 在线表单
4. **组织验证**（1–5 工作日）：
   - 企业注册信息核查
   - 电话验证（CA 拨打企业公开电话确认签署人身份）
5. **颁发证书**：下载或硬件 token 寄送

### 2.2 EV Code Signing 申请流程（额外步骤）

- 需要 DUNS 编码（必须）
- 物理地址验证
- 必须使用 DigiCert 提供的 FIPS 140-2 USB token（包含在费用中）
- 签署人需提供政府签发身份证件
- 处理时间：5–15 个工作日

### 2.3 自签名证书生成（仅限内部测试）

```powershell
# 生成自签名代码签名证书（仅测试用，SmartScreen 不信任）
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=AdAssistant Test" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyUsage DigitalSignature `
    -KeySpec Signature

# 导出 PFX（需设置密码）
$password = ConvertTo-SecureString -String "PLACEHOLDER_TEST_PASSWORD" -Force -AsPlainText
Export-PfxCertificate `
    -Cert $cert `
    -FilePath "D:\APPLICATION\ad-assistant-test-cert.pfx" `
    -Password $password
```

> ⚠️ **重要**：自签名证书仅用于 CI 流水线预发布验证和签名命令测试。分发版本绝不使用自签名证书。

---

## 3. 私钥保护策略

### 3.1 策略对比

| 策略 | 安全级别 | 成本 | CI 集成难度 | 建议阶段 |
|------|---------|------|-----------|---------|
| **硬件 USB Token (EV)** | ⭐⭐⭐⭐⭐ 极高 | 包含在 EV 证书费中 | ⚠️ CI 不可用（需物理插入） | v1.0.x 正式商业发布 |
| **Azure Key Vault / AWS KMS** | ⭐⭐⭐⭐ 高 | ~$3–30/月 | ✅ CI 通过 Managed Identity | v0.2.x 付费试点（推荐） |
| **加密 PFX + CI Secret** | ⭐⭐⭐ 中 | 免费 | ✅ CI secrets 变量 | v0.2.x 付费试点（备选） |
| **本地 PFX（未加密）** | ⭐ 低 | 免费 | ❌ 不能用于 CI | ❌ 不推荐 |

### 3.2 推荐：Azure Key Vault + Managed Identity（中期 v0.2.x）

```
┌─────────────────────────────────────────────────────┐
│                    CI Pipeline                        │
│  (GitHub Actions / Self-hosted Runner)               │
│                                                       │
│  1. Managed Identity / OIDC → Auth to Key Vault     │
│  2. Download certificate (no private key export)     │
│  3. signtool sign /f <cert> /csp "..." /k "..."     │
│  4. Verify signature                                  │
│  5. Cert auto-destroyed after build                  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│               Azure Key Vault                        │
│  - Certificate: ad-assistant-code-sign-ov           │
│  - Private key: HSM-protected, non-exportable       │
│  - Access: Managed Identity only (RBAC)             │
│  - Audit logging: enabled                            │
└─────────────────────────────────────────────────────┘
```

### 3.3 备选：加密 PFX + CI Secret（简单场景）

```yaml
# .github/workflows/release.yml（模板示例，不提交真实凭据）
env:
  PFX_BASE64: ${{ secrets.CODE_SIGNING_PFX_BASE64 }}
  PFX_PASSWORD: ${{ secrets.CODE_SIGNING_PFX_PASSWORD }}
```

> ⚠️ 绝对禁止将 PFX 文件或密码提交到仓库。PFX base64 通过 CI secrets 注入，仅在构建时临时解码到 `$RUNNER_TEMP`，构建结束后立即删除。

---

## 4. Tauri Bundle 签名配置

### 4.1 Tauri 原生签名支持

Tauri v2 的 `tauri.conf.json` 支持通过 `bundle.windows.wix` 和 `bundle.windows.nsis` 配置签名工具链。

> **当前状态**：本项目 Tauri 配置 (`tauri.conf.json`) 不包含签名配置。以下模板仅供后续实现参考，**不在本任务中实际修改**。

### 4.2 配置模板（参考用）

```json
{
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/icon.ico",
      "icons/icon.png"
    ],
    "windows": {
      "signCommand": "signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f %CERT_PATH% /p %CERT_PASSWORD% %1",
      "wix": {
        "language": "en-US"
      },
      "nsis": {
        "installerIcon": "icons/icon.ico"
      }
    }
  }
}
```

> **注意**：`signCommand` 仅对 NSIS 安装程序生效（`%1` = NSIS 生成的 setup.exe）。MSI 签名需额外步骤（见 5.4）。

### 4.3 Tauri 环境变量注入

Tauri 2 支持通过环境变量注入签名参数，避免将路径写入配置：

```powershell
# Windows 本地签名
$env:CERT_PATH = "D:\APPLICATION\code-signing\ad-assistant-ov.pfx"
$env:CERT_PASSWORD = "PLACEHOLDER"
npm run tauri build
```

CI 中等效的 GitHub Actions 步骤：

```yaml
- name: Decode PFX
  run: |
    echo "${{ secrets.PFX_BASE64 }}" | base64 -d > $env:RUNNER_TEMP\cert.pfx
- name: Build with signing
  env:
    CERT_PATH: ${{ runner.temp }}\cert.pfx
    CERT_PASSWORD: ${{ secrets.PFX_PASSWORD }}
  run: npm run tauri build
```

---

## 5. 签名命令模板

### 5.1 工具链要求

签名需要 Windows SDK 中的 SignTool：

```powershell
# 确认 signtool 可用（Windows SDK 10+）
where signtool
# 典型路径：C:\Program Files (x86)\Windows Kits\10\bin\10.0.x\x64\signtool.exe
```

### 5.2 基础签名命令（PFX）

```powershell
# 签名 EXE / DLL / MSI / NSIS installer
signtool sign `
    /fd SHA256 `                    # 摘要算法
    /tr http://timestamp.digicert.com `  # RFC 3161 时间戳
    /td SHA256 `                    # 时间戳摘要
    /f "D:\APPLICATION\code-signing\ad-assistant.pfx" `  # PFX 路径
    /p "PLACEHOLDER_PASSWORD" `     # PFX 密码
    /v `                            # 详细输出
    "D:\Project\ad-assistant\desktop-app\src-tauri\target\release\bundle\*.*"
```

### 5.3 使用 Azure Key Vault 签名（无本地 PFX）

```powershell
# 通过 Azure Code Signing (ACS) 或 signtool + KSP
signtool sign `
    /fd SHA256 `
    /tr http://timestamp.digicert.com `
    /td SHA256 `
    /csp "Microsoft Software Key Storage Provider" `
    /k "[KeyName]" `
    /v `
    "%1"
```

### 5.4 多产物签名脚本

```powershell
# sign_all.ps1（模板 — 路径为占位符，不提交真实密码）
param(
    [Parameter(Mandatory=$true)]
    [string]$CertPath,
    [Parameter(Mandatory=$true)]
    [string]$CertPassword
)

$releaseDir = "D:\Project\ad-assistant\desktop-app\src-tauri\target\release"
$files = @(
    "$releaseDir\ad-assistant-desktop.exe",
    "$releaseDir\bundle\msi\AdAssistant_*_x64_en-US.msi",
    "$releaseDir\bundle\nsis\AdAssistant_*_x64-setup.exe"
)

foreach ($file in (Get-ChildItem -Path $files -ErrorAction SilentlyContinue)) {
    Write-Host "Signing: $($file.FullName)"
    signtool sign `
        /fd SHA256 `
        /tr http://timestamp.digicert.com `
        /td SHA256 `
        /f $CertPath `
        /p $CertPassword `
        /v `
        $file.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Signing failed for $($file.Name)"
        exit 1
    }
}

Write-Host "All files signed successfully."
```

---

## 6. 签名验证

### 6.1 验证命令

```powershell
# 验证签名有效性
signtool verify /pa /v "D:\Project\ad-assistant\desktop-app\src-tauri\target\release\ad-assistant-desktop.exe"
signtool verify /pa /v "D:\Project\ad-assistant\desktop-app\src-tauri\target\release\bundle\msi\AdAssistant_0.1.0_x64_en-US.msi"
signtool verify /pa /v "D:\Project\ad-assistant\desktop-app\src-tauri\target\release\bundle\nsis\AdAssistant_0.1.0_x64-setup.exe"
```

### 6.2 验证通过标准

- `/pa` 表示使用 Windows 默认验证策略
- 输出中应显示 `Successfully verified: <path>`
- 签名者信息包含正确的组织名称
- 时间戳有效（`Timestamp: ... verified`）
- 证书链受信任，且未过期

### 6.3 PowerShell 脚本验证

```powershell
# 批量验证 +
$files = Get-ChildItem -Path "D:\Project\ad-assistant\desktop-app\src-tauri\target\release\" `
    -Include "*.exe", "*.msi", "*.dll" -Recurse

foreach ($file in $files) {
    $result = & signtool verify /pa $file.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $($file.Name)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($file.Name) — UNSIGNED" -ForegroundColor Red
    }
}
```

---

## 7. 时间戳服务

时间戳确保签名在证书过期后依然有效（只要签名时证书有效 + 签名加了时间戳）。

### 7.1 推荐时间戳服务器

| CA | RFC 3161 URL | 备注 |
|----|-------------|------|
| DigiCert | `http://timestamp.digicert.com` | 推荐，免费，高可用 |
| Sectigo | `http://timestamp.sectigo.com` | 免费 |
| GlobalSign | `http://timestamp.globalsign.com/tsa/r6advanced1` | 免费 |
| Comodo | `http://timestamp.comodoca.com` | Sectigo 旗下 |

> 优先使用 `http://`（非 `https://`），因为时间戳服务器通常在无 TLS 环境下可靠性更高（签名操作本身包含防篡改）。

---

## 8. SmartScreen 风险说明

### 8.1 当前未签名状态

```
用户下载未签名安装包 → SmartScreen 拦截 → "Windows protected your PC"
                                                     ↓
                                        用户点击 "More info" → "Run anyway"
                                                    ↓
                                        仅高级用户会继续，普通用户流失
```

### 8.2 签名后预期改善

| 阶段 | 证书类型 | SmartScreen 行为 | 用户流失率估算 |
|------|---------|-----------------|-------------|
| 当前 | 未签名 | "Windows protected your PC" 拦截 | 30–60% |
| 签名后立即（OV） | OV Code Signing | 仍显示 "not commonly downloaded" | 15–30% |
| 签名后 2–6 周（OV） | OV Code Signing | SmartScreen 信誉累积后无警告 | 5–10% |
| 签名后立即（EV） | EV Code Signing | 无 SmartScreen 警告 | < 5% |
| 微软 App Store (future) | Store signing | 零警告 | 0% |

### 8.3 SmartScreen 信誉累积因素

- 下载量和下载频率
- 签名证书信誉历史
- 文件是否包含恶意特征
- 安装后的遥测反馈（崩溃率、保留率）

---

## 9. CI/CD 集成方案

### 9.1 安全原则

1. 私钥只能通过 CI secrets 注入，绝不写入配置文件
2. 签名步骤在隔离的构建阶段执行
3. 构建后验证签名并在日志中打印结果
4. 签名完成后立即清理临时 PFX 文件
5. 限制 CI secrets 访问权限（仅 main/release 分支可读取）

### 9.2 GitHub Actions 签名流程模板

```yaml
# 模板示例 — 仅供后续实现参考
# 此文件不应作为 .github/workflows/*.yml 提交（S05-R07 禁改 CI 配置）

# jobs:
#   build-and-sign:
#     runs-on: windows-latest
#     environment: release  # Protection rule: requires approval
#     steps:
#       - uses: actions/checkout@v4
#       - name: Setup Node.js
#         uses: actions/setup-node@v4
#       - name: Install dependencies
#         run: npm ci
#       - name: Decode PFX
#         run: |
#           [System.Convert]::FromBase64String("${{ secrets.CODE_SIGNING_PFX_BASE64 }}") `
#             | Set-Content "$env:RUNNER_TEMP\cert.pfx" -Encoding Byte
#       - name: Tauri Build
#         env:
#           CERT_PATH: ${{ runner.temp }}\cert.pfx
#           CERT_PASSWORD: ${{ secrets.CODE_SIGNING_PFX_PASSWORD }}
#         run: npm run tauri build
#       - name: Sign MSI
#         run: |
#           signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
#             /f $env:CERT_PATH /p $env:CERT_PASSWORD /v `
#             src-tauri\target\release\bundle\msi\*.msi
#       - name: Verify signature
#         run: signtool verify /pa /v src-tauri\target\release\bundle\**\*.exe
#       - name: Cleanup PFX
#         if: always()
#         run: Remove-Item "$env:RUNNER_TEMP\cert.pfx" -Force -ErrorAction SilentlyContinue
```

---

## 10. 决策时间线与建议

### 10.1 分阶段实施计划

```
内测 v0.1.x (当前)          →  不签名
    │                              用户手动 "Run anyway"
    │                              关注：签名任务发布阻塞项
    │
付费试点 v0.2.x 前 (约 1-2 月)  →  获取 OV 证书
    │                              配置 CI secrets
    │                              启用 Tauri signCommand
    │                              目标：SmartScreen 信誉累积 ≥ 60 天
    │
正式商业发布 v1.0.x 前          →  评估 EV 证书（若免 SmartScreen 有 ROI）
    │                              考虑 Azure Key Vault
    │                              考虑微软商店发布
```

### 10.2 前置依赖

- [ ] 企业营业执照（或个体工商户执照）
- [ ] DUNS 编码（EV 必须，OV 可选）
- [ ] CA 预算审批（$200–600/年）
- [ ] CI 密钥权限已授权（仅 release maintainer）
- [ ] 签名构建时间预算（签名步骤增加 ≤ 30 秒/构建）

### 10.3 阻塞项（需用户决策）

1. **证书类型选择**：OV 还是 EV？
2. **供应商选择**：DigiCert / Sectigo / GlobalSign？
3. **私钥存储方案**：Azure Key Vault（推荐）/ CI secrets / 硬件 token？
4. **预算**：年度证书费用审批
5. **时间**：证书申请和颁发周期（1–15 工作日）

---

## 11. 残余风险

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| SmartScreen 信誉累积慢（OV 证书） | 中 | 尽早获取 OV 证书，在 v0.2 前至少 60 天 |
| CI secrets 泄露导致私钥泄露 | 高 | 使用 environment protection rules + 构建后清理 |
| 证书过期未续期 | 高 | 设置 CA 续期提醒（证书到期前 30 天 + 7 天双重通知） |
| 时间戳服务不可用（签名失败） | 低 | 配置 2 个 fallback 时间戳 URL |
| CA 验证失败（企业信息不全） | 中 | 提前准备营业执照翻译件 + DUNS |
| OV 证书 SmartScreen 信誉始终不达标 | 低 | 决策点：升级 EV 或申请微软商店 |
| 不同 CA 的交叉签名兼容性 | 低 | 使用主流 CA (DigiCert/Sectigo)，避免小 CA |

---

## 12. 安全说明

- **本文档不包含任何真实证书、私钥、密码或 token**
- 所有路径和密码均为 `PLACEHOLDER` 占位符
- 签名命令模板中使用 `PLACEHOLDER_PASSWORD` 替代真实密码
- PFX/P12 文件绝不提交到仓库
- `tauri.conf.json` 中的 `signCommand` 通过环境变量注入凭据，不硬编码
- CI secrets 通过 GitHub environment protection rules 限制访问
- 签名验证作为独立 CI 步骤运行，失败则阻塞发布
