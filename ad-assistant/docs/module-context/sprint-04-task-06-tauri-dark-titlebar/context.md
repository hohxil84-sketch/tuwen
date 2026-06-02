# S04-T06: Tauri 深色标题栏 — 模块上下文

## 状态

`BLOCKED_NEEDS_TAURI_SOURCE`

## 审计日期

2026-06-02

## 审计结果

### 目录结构

`desktop-app/src-tauri/` 目录当前内容：

| 路径 | 类型 | 说明 |
|------|------|------|
| `.gitkeep` | 占位文件 | Sprint-01 骨架，明确标注 "no Tauri config created yet" |
| `target/` | 构建产物 | 包含 `.rustc_info.json`、`CACHEDIR.TAG`、`debug/`（禁止修改） |

### 缺失的 Tauri 源配置文件

以下文件均不存在：

- `tauri.conf.json` — 无
- `tauri.conf.json5` — 无
- `Cargo.toml` — 无
- `src/main.rs` — 无
- `src/lib.rs` — 无
- `capabilities/*.json` — 无

### package.json 中的 Tauri 支持

`desktop-app/package.json` 当前：

- 无 `@tauri-apps/cli` 依赖
- 无 `@tauri-apps/api` 依赖
- 无 `tauri` 或 `tauri dev` 或 `tauri build` scripts
- 仅有 `vite` + `vue-tsc` 纯前端构建链

### .gitkeep 内容

```
# Tauri 2 configuration directory
# Sprint-01: skeleton only — no Tauri config created yet
#
# WARNING: Modifying Tauri permissions is a MAJOR CHANGE.
# Must confirm with user before any changes to this directory.
```

## 阻塞原因

Tauri 源配置文件不存在，无法对窗口标题栏/系统 chrome 做任何配置变更。Tauri 窗口的深色标题栏需要修改 `tauri.conf.json` 中 `windows[].decorations`、`windows[].titleBarStyle` 或相关配置项，但这些文件尚未创建。

## 未采用的方案

由于源文件不存在，以下方案均无法实施：

1. **Tauri 2 原生 `titleBarStyle: "overlay"`** — 需要 `tauri.conf.json` 中 windows 配置段
2. **`decorations: false` + 自定义标题栏** — 需要 Tauri 配置 + `src/main.rs` 窗口事件逻辑 + Vue 自定义标题栏组件
3. **Windows 原生深色标题栏（DwmSetWindowAttribute）** — 需要 `Cargo.toml` 添加 windows-rs 依赖 + `src/main.rs` 窗口创建逻辑

## 未触碰的文件

根据任务单规定，以下均未修改：

- `desktop-app/src-tauri/target/**` — 未触碰
- `cloud-backend/**` — 未触碰
- `shared/**` — 未触碰
- `desktop-app/local-service/**` — 未触碰
- `desktop-app/package.json` — 未触碰
- 任何依赖或 lockfile — 未触碰

## 测试结果

- `npm run build`（desktop-app）：68 modules, 0 errors ✅
- `git diff --check`：通过 ✅
- `npm run tauri dev`：不可用（无 Tauri CLI 依赖，无 Tauri 源配置）

## 建议的后续任务

1. **Tauri 工程初始化**（需用户/Codex 单独起草任务单）：
   - 安装 `@tauri-apps/cli` 和 `@tauri-apps/api`
   - 运行 `cargo init` 或 Tauri CLI 初始化
   - 生成 `tauri.conf.json`、`Cargo.toml`、`src/main.rs`、`src/lib.rs`、`capabilities/`
   - 配置窗口标题栏深色方案
2. **替代方案**（无需 Tauri 重建）：
   - 在 Vue 前端层面通过 CSS `color-scheme: dark` + meta `theme-color` 提示浏览器使用深色主题
   - 注意：此方案仅影响 Web 版，Tauri 原生标题栏仍需 Tauri 源配置

## 残余风险

- 桌面端当前在 Windows 上运行时，顶部系统标题栏为白色/浅色，与深色 SaaS 工作台 UI 不一致
- 此风险已在 `docs/sprint-03-summary.md` 和 `docs/26-desktop-dashboard-ui-redesign.md` 中记录
- 在 Tauri 工程初始化完成前，此视觉问题无法通过本任务范围解决

## 回滚方式

无需回滚 — 本任务未修改任何代码或配置文件。
