# S04-T08: Tauri 打包与 EXE Smoke 验证

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 分支

`feature/sprint-04-task-08-tauri-package-smoke`

## 目标

确认当前桌面端是否已具备生成本地 Windows EXE / 安装包的基础能力。

## 主要改动

### tauri.conf.json — Bundle 配置

- `bundle.active`: `false` → `true`
- `bundle.targets`: 新增 `"all"`（生成 MSI + NSIS）
- `productName`: `"AI广告助手"` → `"AdAssistant"`（ASCII）
  - 原因：WiX v3 不支持 codepage 1252 以外的字符；中文产品名在 MSI 构建时导致 LGHT0311 错误

### 其他文件

- `docs/17-release-and-update.md`：新增本地打包 Smoke 章节
- `docs/09-desktop-app-guide.md`：新增打包命令说明
- `docs/module-context/sprint-04-task-08-tauri-package-smoke/context.md`（本文件）
- `PROGRESS.md`：进度记录

## 构建产物

### 生成路径

| 产物 | 绝对路径（开发机） | 文件类型 |
|------|-------------------|----------|
| 裸 EXE | `desktop-app/src-tauri/target/release/ad-assistant-desktop.exe` | Windows x64 二进制 |
| MSI | `desktop-app/src-tauri/target/release/bundle/msi/AdAssistant_0.1.0_x64_en-US.msi` | Windows Installer |
| NSIS | `desktop-app/src-tauri/target/release/bundle/nsis/AdAssistant_0.1.0_x64-setup.exe` | NSIS 安装程序 |

### 构建命令

```bash
cd desktop-app
npm run tauri build
```

### 构建流程

1. `beforeBuildCommand` → `vue-tsc --noEmit && vite build`（前端类型检查 + Vite 打包）
2. `cargo build --release` → 编译 Rust 源码为 `ad-assistant-desktop.exe`
3. WiX `candle.exe` + `light.exe` → MSI 安装包
4. NSIS `makensis.exe` → NSIS 安装包

### 首次构建用时

- Cargo release 编译（355 crates）：~3 分钟
- WiX + NSIS 打包：~2 分钟
- 后续增量构建（仅变更前端）：~1 分钟

## Bundle 配置快照

```json
{
  "productName": "AdAssistant",
  "version": "0.1.0",
  "identifier": "com.ad-assistant.desktop",
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/icon.ico", "icons/icon.png"]
  }
}
```

## 验证结果

### 自动化验证

- `npm run build`（Vite）：74 modules, 0 errors ✅
- `npm run tauri build`：exit 0，全部 2 bundle 格式成功 ✅
- Cargo release 编译：成功 ✅
- WiX candle + light：成功（ASCII productName 修复后）✅
- NSIS makensis：成功 ✅

### 人工验证

- [ ] 启动生成的 EXE，确认主窗口可打开
- [ ] 确认深色标题栏可见（frameless + decorations: false）
- [ ] 确认最小化按钮可用
- [ ] 确认最大化/还原按钮可用
- [ ] 确认关闭按钮可用
- [ ] 确认窗口可通过标题栏拖拽移动

> **注**：终端环境无法完成 GUI 人工验证，需用户在 Windows 桌面环境执行。

## 已知问题与限制

### productName 仅支持 ASCII

- **根因**：WiX v3 的 `light.exe` 默认 codepage 为 1252（Latin-1），不兼容中文产品名
- **错误信息**：`LGHT0311: A string was provided with characters that are not available in the specified database code page '1252'`
- **当前方案**：`productName` 设为 ASCII `"AdAssistant"`
- **窗口标题**：不受影响，仍为 `"AI 图文广告助手"`（由 `app.windows[0].title` 独立控制）
- **未来可选方案**：
  - 仅使用 NSIS（不生成 MSI），NSIS 无 codepage 限制
  - 升级到 WiX v4（支持原生 UTF-8）
  - 修改 `locale.wxl` 的 `TauriCodepage` 为 65001（UTF-8），需自定义 Tauri 打包流程

### 占位图标

- 当前使用 Tauri 默认图标（`icon.ico` + `icon.png`），未替换为品牌图标
- 后续任务：S04-T09（品牌图标替换）

### frameless 窗口无原生阴影

- S04-T07 已知残余风险，打包后依旧存在
- 无系统窗口菜单、无原生窗口阴影

### 无代码签名

- 构建产物未签名
- Windows SmartScreen 可能弹出 "Windows 已保护你的电脑" 警告
- 不影响功能验证（用户可选择 "仍要运行"）

## 未实现内容

按任务单 What Not To Build：
- 未做正式发布
- 未上传、分发或签名安装包
- 未配置自动更新
- 未配置 updater endpoint、签名私钥或发布通道
- 未做代码签名证书接入
- 未做 MSI / NSIS 深度定制主题
- 未接入 sidecar
- 未修改本地 Python 服务启动方式
- 未修改后端、数据库、shared DTO、Provider、Auth、Credit、Payment 或 CI
- 未提交 `desktop-app/src-tauri/target/**`、`desktop-app/dist/**` 或任何构建产物

## 残余风险和回滚

### 残余风险

- WiX v3 codepage 限制 → productName 必须 ASCII
- 占位图标 → 打包产物显示 Tauri 默认图标
- 无代码签名 → 分发场景受限

### 回滚方式

- revert 本任务 commit 可恢复打包配置和文档记录
- 仅关闭打包：恢复 `tauri.conf.json` 中 `bundle.active = false`
- 本地生成的 `target/**` 和 `dist/**` 未提交，无需回滚
- 不影响数据库、远端发布、用户数据

## 扩展入口

- Bundle 配置入口：`desktop-app/src-tauri/tauri.conf.json` → `bundle` 字段
- 产品元数据：`productName`、`version`、`identifier`
- 安装包定制：Tauri 2 NSIS/WiX 插件配置
- 图标替换：`desktop-app/src-tauri/icons/` 目录
- 发布文档：`docs/17-release-and-update.md`
