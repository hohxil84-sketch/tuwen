# 17 发布与更新

## 发布原则

发布必须可回滚、可追踪、可灰度。

## 桌面端更新

修改自动更新逻辑属于重大变更，必须先确认。

桌面端发布必须检查：
- Tauri 权限
- 本地服务启动方式
- sidecar 签名
- 安装包来源
- 版本号
- 更新通道
- **代码签名**：EXE/MSI/NSIS 必须签名（内测阶段可跳过，见 [29-code-signing-plan.md](29-code-signing-plan.md)）

## 本地打包 Smoke（S04-T08）

当前桌面端已通过最小本地打包验证，可生成 Windows 安装包。

### 构建命令

```bash
cd desktop-app
npm run tauri build
```

### 产物

构建产品位于 `desktop-app/src-tauri/target/release/`：

| 产物 | 相对路径（project root） | 类型 |
|------|--------------------------|------|
| 应用 EXE | `desktop-app/src-tauri/target/release/ad-assistant-desktop.exe` | 裸二进制 |
| MSI 安装包 | `desktop-app/src-tauri/target/release/bundle/msi/AdAssistant_0.1.0_x64_en-US.msi` | Windows Installer |
| NSIS 安装包 | `desktop-app/src-tauri/target/release/bundle/nsis/AdAssistant_0.1.0_x64-setup.exe` | NSIS 安装程序 |

### 已知限制

- **productName 仅支持 ASCII**：当前 `tauri.conf.json` 的 `productName` 为 `"AdAssistant"`（ASCII）。WiX v3（MSI 打包工具）不兼容中文产品名称（codepage 1252 限制）。如需中文产品名出现在 Windows 安装程序中，需升级到 WiX v4（支持 UTF-8）或仅使用 NSIS 安装包。
- **内测图标已替换**：S04-T09 已将 Tauri 默认占位图标替换为内测品牌图标（暗色背景 + 几何 "A" 字标识）。正式品牌图标仍待确认。
- **frameless 窗口无原生阴影**：已知 S04-T07 残余风险，打包后窗口仍无系统级阴影和菜单。S04-T10 已通过 CSS 内描边 + 内阴影提供最小视觉边界（不等同于 Windows 原生窗口阴影，正式方案需 DWM API 或 Tauri 插件）。
- **不包含自动更新**：当前 bundle 未配置 updater endpoint 和签名私钥。
- **未经代码签名**：打包产物未签名，Windows SmartScreen 可能弹出警告。代码签名方案详见 [docs/29-code-signing-plan.md](29-code-signing-plan.md)。

### 人工验证要点

安装或直接启动 EXE 后，应确认：
- [ ] 应用主窗口正常打开
- [ ] 深色工作台背景覆盖整个窗口（frameless）
- [ ] 自定义标题栏可见（data-tauri-drag-region 区域可拖拽）
- [ ] 最小化、最大化/还原、关闭按钮可用
- [ ] 窗口可拖拽移动

## 云端发布

云端发布必须检查：
- 数据库迁移
- Provider 配置
- API 兼容性
- 限流配置
- 日志脱敏
- 回滚方案

## 版本策略

建议版本：
- `0.1.x`：MVP 内测
- `0.2.x`：付费试点
- `1.0.x`：正式商业发布

## 代码签名

所有桌面端发布产物（EXE/MSI/NSIS）在正式分发前必须代码签名。

签名方案详见 [docs/29-code-signing-plan.md](29-code-signing-plan.md)，包括：
- 证书类型选择（EV vs OV vs 自签名）
- 私钥保护策略（Azure Key Vault / 加密 PFX）
- Tauri 签名配置模板
- 签名和验证命令
- SmartScreen 风险说明
- CI/CD 集成方案

当前未实现。内测阶段用户通过手动 `Run anyway` 绕过 SmartScreen 警告。

## 发布前闸门

必须通过：
- 登录授权测试
- 设备绑定测试
- OCR 最小闭环测试
- 额度扣除或免费记录测试
- provider_call_log 写入测试
- 安全检查

