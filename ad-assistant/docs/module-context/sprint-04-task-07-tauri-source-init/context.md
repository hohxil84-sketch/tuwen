# S04-T07: Tauri 工程源配置初始化与深色标题栏恢复 — 模块上下文

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 日期

2026-06-02

## 分支

`feature/sprint-04-task-07-tauri-source-init`

## 初始化方式

手动创建最小 Tauri 2 源配置文件（未使用 `cargo tauri init` 或 `npm create tauri-app`），确保只生成任务单允许范围内的文件。

## Tauri 源文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `src-tauri/Cargo.toml` | Rust 项目配置，依赖 tauri 2、serde、serde_json | 新建 |
| `src-tauri/Cargo.lock` | Rust 依赖锁定（自动生成） | 新建（已提交） |
| `src-tauri/build.rs` | tauri-build 构建脚本 | 新建 |
| `src-tauri/src/main.rs` | Rust 入口，windows_subsystem 配置 | 新建 |
| `src-tauri/src/lib.rs` | Tauri Builder 入口 | 新建 |
| `src-tauri/tauri.conf.json` | Tauri 2 窗口/构建/安全配置 | 新建 |
| `src-tauri/capabilities/default.json` | 最小权限声明 | 新建 |
| `src-tauri/icons/icon.ico` | Windows 应用图标（32x32） | 新建 |
| `src-tauri/icons/icon.png` | 通用图标（128x128） | 新建 |
| `src-tauri/.gitignore` | 忽略 target/ 构建产物 | 新建 |
| `src-tauri/gen/schemas/` | tauri-build 生成的 JSON Schema 缓存 | 自动生成 |

## 标题栏 / 窗口 chrome 方案

**采用方案：frameless 窗口 + 自定义标题栏**

### 配置

- `tauri.conf.json` 中 `app.windows[0].decorations = false`（无系统标题栏）
- `app.windows[0].backgroundColor = "#07111f"`（与 `--bg-app` 一致）

### 前端适配

- **AppTopbar.vue**：添加 `data-tauri-drag-region` 拖拽区域 + 窗口控制按钮（最小化/最大化/还原/关闭）
- 窗口控制按钮通过 `@tauri-apps/api/window` 调用原生窗口操作
- 浏览器开发模式下自动隐藏窗口控制按钮（`window.__TAURI_INTERNALS__` 检测）
- **vite.config.ts**：添加 `server.watch.ignored: ["**/src-tauri/target/**"]` 避免文件监控器 EBUSY 冲突

### 未采用方案

- **系统标题栏深色化**：Windows 标题栏颜色跟随系统主题，Tauri 2 无法通过配置强制深色
- **`titleBarStyle: "overlay"`**：Tauri 2 此选项主要用于 macOS，Windows 上效果有限

## capabilities 权限清单

| 权限 | 用途 | 是否最小化 |
|------|------|-----------|
| `core:default` | Tauri 核心运行 | ✅ 必需 |
| `core:window:default` | 窗口基础操作 | ✅ 必需 |
| `core:window:allow-minimize` | 自定义最小化按钮 | ✅ |
| `core:window:allow-toggle-maximize` | 自定义最大化/还原按钮 | ✅ |
| `core:window:allow-close` | 自定义关闭按钮 | ✅ |
| `core:window:allow-is-maximized` | 检测窗口状态用于图标切换 | ✅ |
| `core:window:allow-set-fullscreen` | 保留，未在当前 UI 暴露 | ✅（预置） |
| `core:window:allow-start-dragging` | 兼容性预留 | ✅ |

未开放的权限：`shell`、`fs`、`path`、`http`、`clipboard`、`notification`、`global-shortcut`、`updater`

## 新增依赖

### npm

| 包名 | 版本 | 类型 |
|------|------|------|
| `@tauri-apps/api` | ^2.0.0 → 2.11.0 | dependency |
| `@tauri-apps/cli` | ^2.0.0 → 2.11.2 | devDependency |

- 新增 script: `"tauri": "tauri"`
- `package-lock.json` 已自动更新

### Cargo

| crate | 版本 |
|-------|------|
| tauri | 2.11.2 |
| tauri-build | 2.6.2 |
| serde | 1.x |
| serde_json | 1.x |
| + 400+ 传递依赖 | — |

## 超出 allowed files 的文件

| 文件 | 原因 | 风险 |
|------|------|------|
| `desktop-app/vite.config.ts` | Tauri dev 需要忽略 target/ 避免 Vite 文件监控器 EBUSY 冲突 | 低 — 仅新增 3 行 watch 配置，不改变构建行为 |

## 验证结果

| 测试 | 命令 | 结果 |
|------|------|------|
| 前端构建 | `npm run build` | 74 modules, 0 errors ✅ |
| 空白检查 | `git diff --check` | 通过 ✅ |
| Tauri 编译 | `cargo build`（通过 tauri dev） | 355 crates 编译成功 ✅ |
| Tauri 启动 | `npm run tauri dev` | exit 0，desktop-app 进程已启动 ✅ |
| 窗口外观 | 人工目视 | frameless 窗口无系统标题栏，深色工作台覆盖整个窗口区域 ✅ |
| API 代理 | Vite proxy | ECONNREFUSED（预期，云端后端未运行） ✅ 非阻塞 |

## 桌面端开发指南

### 启动 Tauri 开发模式

```powershell
cd ad-assistant/desktop-app
npm run tauri dev
```

### 仅前端开发（浏览器模式）

```powershell
cd ad-assistant/desktop-app
npm run dev
```

浏览器模式下窗口控制按钮自动隐藏，不影响开发体验。

## 残余风险

1. **自定义标题栏无窗口菜单**：右键标题栏无系统上下文菜单（还原/移动/大小/关闭），这是 frameless 窗口的固有限制
2. **窗口阴影**：frameless 窗口在部分 Windows 版本下可能缺少原生窗口阴影
3. **窗口控制按钮在窄窗口下可能被遮挡**：当前 min-width 1024px，控制按钮与退出按钮间距固定
4. **图标为极简占位**：正式发布前需替换为品牌图标

## 回滚方式

- revert 本任务 commit 即可移除所有 Tauri 源配置、依赖和前端标题栏适配
- 如果仅需回滚标题栏方案，可将 `tauri.conf.json` 中 `decorations` 改为 `true`，并移除 AppTopbar.vue 中窗口控制按钮代码

## 后续任务建议

1. S04-T08: Tauri 打包与 EXE 生成（需单独任务单）
2. 图标替换为品牌图标
3. 窗口阴影修复（如需要）
