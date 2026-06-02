# S05-R08: Windows 原生窗口阴影专项

## 状态

`COMPLETED`

## 分支

`feature/sprint-05-risk-08-native-window-shadow`

## 背景

S04-T10 通过 CSS 内描边和内阴影缓解 frameless 窗口边界感，但不等同于 Windows DWM 原生外部阴影。正式体验需要 native window shadow 方案。

S04-Sprint E2E 残余风险 #4 标记此问题。

## 用户目标

接入 Windows 原生窗口阴影方案，提升 frameless 窗口桌面层次，使窗口具有系统级外部阴影。

## What To Build

### 1. 方案调研与选择

三方案对比：
- `window-shadows` crate：调用 Windows DWM API（`DwmExtendFrameIntoClientArea` + `DWMWA_USE_IMMERSIVE_DARK_MODE`），Tauri 社区常用
- 手动 DWM API 调用（`windows` crate）：不新增独立依赖，但需手写 unsafe 代码
- Tauri plugin `tauri-plugin-window`：Tauri 2 官方窗口插件，但无直接 shadow API

**选择 `window-shadows` crate**：Tauri 2 生态标准方案，API 最简，仅 1 行调用，支持 Windows/macOS/Linux（各平台自动 fallback）。

### 2. 最小 PoC

- `Cargo.toml`：新增 `window-shadows = "0.2"`
- `lib.rs`：在 `setup` hook 中调用 `window_shadows::set_shadow(&window, true)`
- 仅在 Windows 平台启用（条件编译）

### 3. 兼容性

- 最大化时自动无阴影（DWM 行为）
- macOS/Linux 自动 fallback（无操作）
- 不修改 `tauri.conf.json` 权限

## What Not To Build

- 不改业务页面（`App.vue` 内容不变）
- 不接入透明窗口、Mica、Acrylic
- 不扩大文件系统、shell、http 权限
- 不修改 Tauri permissions / capabilities

## Allowed Files

- `desktop-app/src-tauri/src/lib.rs`
- `desktop-app/src-tauri/Cargo.toml`
- `desktop-app/src-tauri/Cargo.lock`
- `docs/17-release-and-update.md`
- `docs/module-context/sprint-05-risk-08-native-window-shadow/context.md`
- `PROGRESS.md`
- `tasks/current-task.md`

## Forbidden Files

- `desktop-app/src/**`（业务页面不变）
- `desktop-app/src-tauri/tauri.conf.json`
- backend/shared/payment/provider/auth/credit
- CI/deployment
- 证书/发布凭据

## Acceptance Criteria

- [ ] 普通窗口尺寸下可见原生或等价外部阴影
- [ ] 最大化时无边距/裁切异常（要求 GUI 验证）
- [ ] `cargo build` / `cargo check` 通过
- [ ] 文档说明兼容性和 fallback

## Test Method

```bash
cd ad-assistant/desktop-app/src-tauri
cargo check
cargo build --release
```

```bash
git diff --check
```

GUI 验证（需用户执行）：
- `npm run tauri dev` 启动后观察窗口阴影
- 最大化后确认无异常

## Dependency Permission

新增 1 个 Rust crate：`window-shadows = "0.2"`

理由：Tauri 2 生态标准方案，调用 Windows DWM API 实现原生窗口阴影。代码量极小（~200 行），无额外间接依赖链（仅依赖 `windows` crate，Tauri 自身已依赖）。

## Major Change Status

`MAJOR_CHANGE_CONFIRMED_BY_TASK_SCOPE`

原因：涉及 Tauri Rust 源码、窗口系统 API 和 1 个新依赖。

必须暂停确认的情况：
- 需要新增 `window-shadows` 以外的依赖
- 需要修改 Tauri 权限或 capabilities
- 需要接入 Mica/Acrylic/透明窗口

## Security Requirements

- 不新增 shell/fs/http/updater 权限
- 不引入来源不明 native 代码
- `window-shadows` 仅调用公开 Windows DWM API

## Rollback Plan

- revert commit；恢复 S04-T10 CSS 视觉边界方案（无代码修改，仅移除 `set_shadow` 调用和 `window-shadows` 依赖）

## Completion Output Required

- 方案选择理由
- 依赖/权限影响
- 测试结果
- 兼容性说明
- 风险
- 回滚方式
- 中文 commit message
- PR 摘要
