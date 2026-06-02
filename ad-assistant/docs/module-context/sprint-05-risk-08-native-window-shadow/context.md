# S05-R08: Windows 原生窗口阴影专项

## 背景

S04-T10 通过 CSS 内描边 + 内阴影为 frameless 窗口提供最小视觉边界，但不等同于 Windows DWM 原生外部阴影。S04 Sprint E2E 残余风险 #4 标记此问题。

S05-R08 通过 `window-shadows-v2` crate（专为 Tauri 2 设计）调用 Windows DWM API，为 frameless 窗口启用原生平台阴影。

## 方案选择

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| `window-shadows` v0.2 | Tauri 1 生态常用 | 依赖 `raw-window-handle` v0.5，与 Tauri 2（v0.6）不兼容 | ❌ 不适用 |
| `window-shadows-v2` v0.1.1 | 专为 Tauri 2 设计，API 极简（1 行调用），跨平台自动 fallback | 较新（2024），社区规模小 | ✅ **选用** |
| 手动 `windows` crate DWM 调用 | 无额外依赖 | 需手写 unsafe，平台判断复杂，Tauri 版本耦合 | ⚠️ 备选 |

### window-shadows-v2 内部机制

- **Windows**：通过 `HWND` 获取 `raw_window_handle::HasWindowHandle`（v0.6），调用 `DwmExtendFrameIntoClientArea(HWND, MARGINS{1,1,1,1})` 使 DWM 在窗口边缘渲染原生阴影
- **macOS**：设置 `NSWindow.hasShadow = true`
- **Linux**：无操作（平台不支持原生窗口阴影）

## 变更范围

### 修改文件

| 文件 | 变更 |
|------|------|
| `desktop-app/src-tauri/Cargo.toml` | 新增 `window-shadows-v2 = "0.1.1"` |
| `desktop-app/src-tauri/Cargo.lock` | 自动更新（新增 2 packages） |
| `desktop-app/src-tauri/src/lib.rs` | `setup` hook 中调用 `window_shadows_v2::set_shadows(app, true)` |
| `docs/17-release-and-update.md` | 更新 frameless 阴影说明 |
| `docs/module-context/sprint-05-risk-08-native-window-shadow/context.md` | **NEW** — 本文件 |
| `PROGRESS.md` | 进度记录 |
| `tasks/current-task.md` | 状态更新 |

### 未修改

- `tauri.conf.json`：权限未扩展
- `App.vue`：业务页面不变
- CSS 内描边方案保留（S04-T10），native shadow 为补充

## 兼容性

| 平台 | 行为 |
|------|------|
| Windows 10/11 | DWM 原生窗口阴影（深色模式适配） |
| Windows 7/8 | DWM 阴影（如 DWM 可用） |
| macOS | NSWindow 原生阴影 |
| Linux | 无操作（平台不支持） |

- 窗口最大化时 DWM 自动隐藏阴影（无裁切异常）
- 与 S04-T10 CSS 内描边/内阴影共存无冲突

## 依赖

- `window-shadows-v2` v0.1.1：Apache-2.0 OR MIT
- 额外拉取 2 个 crate（包括 `objc2-core-video` for macOS）

## 测试

```bash
cd desktop-app/src-tauri
cargo check         # 通过
cargo build --release  # 通过
git diff --check    # 通过
```

GUI 验证（需用户执行 `npm run tauri dev`）：
- 普通窗口：应可见 DWM 原生外部阴影
- 最大化：无裁切异常
- 最小化/还原：阴影保持正确

## 残余风险

- `window-shadows-v2` 较新，长期维护依赖原作者活跃度
- 阴影效果在不同 Windows 版本和 DPI 缩放下可能有细微差异
- 若未来 Tauri 2 或 `raw-window-handle` API 再次 breaking change，可能需要再次迁移
- 未在 Windows 7/8 上验证
