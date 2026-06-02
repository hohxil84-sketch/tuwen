# S04-T09: Tauri 内测品牌图标替换 — 模块上下文

## 状态

`COMPLETED` — 2026-06-02

## 分支

`feature/sprint-04-task-09-tauri-brand-icon`

## 图标设计

### 设计说明

- 内测图标，非最终品牌 VI
- 设计概念：深色圆角方形背景（匹配应用暗色主题 `#07111f`）+ 几何化 "A" 字标识（AdAssistant 首字母）
- "A" 字采用双色渐变（青 `#00b4d8` 至蓝 `#4895ef`）表达 AI 科技感
- 环绕淡色光环增加层次感
- 小圆点装饰暗示 AI/智能
- 纯 Pillow 生成，无第三方素材、字体或版权依赖

### 图标文件

| 文件 | 路径 | 格式 | 尺寸 |
|------|------|------|------|
| `icon.ico` | `desktop-app/src-tauri/icons/icon.ico` | Windows ICO | 16, 24, 32, 48, 64, 128, 256 px（7 帧） |
| `icon.png` | `desktop-app/src-tauri/icons/icon.png` | PNG RGBA | 128×128 px |

### 生成脚本

`desktop-app/src-tauri/icons/generate_icon.py` — 临时生成脚本，使用 Pillow (`PIL`) 绘制图标。可删除，不参与打包。

### tauri.conf.json 图标引用

`bundle.icon` 配置未变，引用与文件一致：

```json
"icon": [
  "icons/icon.ico",
  "icons/icon.png"
]
```

## 验证结果

### 前端构建

```bash
cd desktop-app && npm run build
```

- 结果：74 modules, 0 errors, built in 1.2s ✅

### Tauri 打包

```bash
cd desktop-app && npm run tauri build
```

- Rust 编译：通过 ✅
- EXE 产物：`desktop-app/src-tauri/target/release/ad-assistant-desktop.exe` (8.2 MB) ✅
- MSI 产物：`desktop-app/src-tauri/target/release/bundle/msi/AdAssistant_0.1.0_x64_en-US.msi` (2.7 MB) ✅
- NSIS 产物：失败 ❌ — GitHub 下载 NSIS 3.11 二进制超时 (network timeout)，与本任务图标变更无关

### 图标有效性

- `icon.ico`：7 尺寸 (16–256 px) ✅
- `icon.png`：128×128 RGBA ✅
- 图标被 Tauri 打包工具正确嵌入 EXE 和 MSI ✅

## 残余风险

- **正式品牌图标缺失**：当前图标为内测占位设计，不替代正式品牌 VI。正式发布前需由设计师提供品牌图标包。
- **NSIS 构建不稳定**：`nsis-3.11.zip` 从 GitHub 下载偶发超时，属于网络/镜像问题，非代码问题。
- **人工验证未执行**：建议在 Windows 上启动 EXE 或安装 MSI，确认任务栏/窗口/安装程序图标显示为新图标而非 Tauri 默认图标。
- **小尺寸可辨识性**：16px 和 24px 图标在最小尺寸下几何细节有限，但 "A" 字形轮廓仍可辨识。

## 回滚方式

1. **快速回滚**：revert 本任务 commit，恢复 `desktop-app/src-tauri/icons/icon.ico` 和 `icon.png` 的上一个版本（Tauri 默认图标）
2. **仅回退图标**：从 `main` 上一个 commit 恢复 `icons/` 目录的两个图标文件
3. 本任务不涉及数据库、API、配置或 UI 变更，无额外回滚步骤
4. `target/**`、`dist/**` 构建产物未提交，清理时确认路径在 `desktop-app/` 构建输出目录内即可

## 相关文档

- [17-release-and-update.md](../../17-release-and-update.md) — 发布与更新，已知限制中的占位图标条目已更新
- [09-desktop-app-guide.md](../../09-desktop-app-guide.md) — 桌面端指南（本任务未修改）
- [PROGRESS.md](../../../PROGRESS.md) — 进度记录

## 自审清单

- [x] 是否只实现了 tasks/current-task.md：是
- [x] 是否任务单由 Codex 起草并字段完整：是
- [x] 是否只修改了 allowed files：是
- [x] 是否没有混入无关文件：是（generate_icon.py 为生成工具，可选保留）
- [x] 是否没有新增未授权依赖：是（仅使用本机已有 Pillow）
- [x] 是否没有触碰未确认的高风险边界：是
- [x] 是否没有 secrets、真实密钥、Token 或生产连接串：是
- [x] 是否完成任务单要求的测试：是（npm run build + npm run tauri build）
- [x] 是否完成 reviewer-mode 自查：待执行
- [x] 是否更新模块上下文：是（本文档）
- [x] 是否追加更新 PROGRESS.md：待执行
- [x] 是否只对 tasks/current-task.md 做了允许的状态类最小更新：是
- [x] 是否列出未实现内容和残余风险：是
