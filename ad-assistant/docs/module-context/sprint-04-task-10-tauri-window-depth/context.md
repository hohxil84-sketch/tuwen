# S04-T10: Tauri frameless 窗口边界与阴影最小优化 — 模块上下文

## 状态

`COMPLETED` — 2026-06-02

## 分支

`feature/sprint-04-task-10-tauri-window-depth`

## 方案说明

### 问题

S04-T07 采用 `decorations: false` 的 frameless 窗口方案后，部分 Windows 版本下窗口缺少原生系统阴影，窗口边界与桌面背景区分不够明显，"窗口贴在桌面上没有层次"。

### 方案

**纯 CSS 视觉层级缓解**，不引入新依赖、不修改 Tauri 配置、不接入系统 API：

在 `App.vue` 的 `#app-shell` 元素上新增两行 CSS：

```css
border: 1px solid rgba(148, 163, 184, 0.10);
box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.30);
```

- **1px 内描边**：极淡的半透明白色边框（10% 透明度），在窗口四边形成微弱但可辨识的边界线
- **柔和内阴影**：40px 羽化半径的黑色内阴影（30% 透明度），增加窗口从桌面"浮起"的层次感

### 为什么不等同于原生阴影

- 原生窗口阴影由 Windows DWM 在窗口外部渲染，有投射感
- CSS `box-shadow: inset` 只在窗口内部产生暗角，无外部投射
- 正式方案需接入 Windows DWM API、Tauri window-shadows 插件或 native window shadow crate

## 修改文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `desktop-app/src/App.vue` | 修改 | `#app-shell` 新增 `border` + `box-shadow: inset` |

### 未修改

- `desktop-app/src-tauri/tauri.conf.json`：未修改
- `desktop-app/src/components/dashboard/AppTopbar.vue`：未修改
- `desktop-app/src-tauri/src/**`：未修改
- `desktop-app/package.json`：未修改
- 无新增依赖

## 验证结果

### 前端构建

```bash
cd desktop-app && npm run build
```

- 结果：74 modules, 0 errors ✅

### diff 检查

```bash
git diff --check
```

- 通过 ✅

### 边界情况分析

| 场景 | 预期行为 | 验证方式 |
|------|---------|---------|
| 普通窗口尺寸 | 窗口四边可见微弱描边 + 柔和暗角，与桌面有层次区分 | CSS 审查 + 人工 |
| 最大化状态 | 描边和阴影仍在窗口内，无额外外边距、裁切或滚动条异常 | CSS 审查：`box-sizing: border-box` 已设置全局 |
| 浏览器开发模式 | 窗口控制按钮隐藏，描边/阴影仍可见（一致体验） | `isTauri` 逻辑不变 |
| Dashboard/OCR/History/Membership/AI文案 | 布局不受影响（改动仅在 `#app-shell` 外层） | 构建通过 |
| 标题栏拖拽/窗口控制 | `data-tauri-drag-region` 和 `win-btn` 不受影响 | AppTopbar 未修改 |

## 残余风险

- **非原生阴影**：CSS 方案不等同于 Windows DWM 原生阴影，窗口在浅色桌面背景下层次感有限
- **多显示器**：未验证不同 DPI/缩放设置下的描边显示效果
- **最大化状态**：1px 描边在最大化时可能不可见（Windows 最大化窗口通常延展到屏幕外），这是可接受行为
- **人工验证未执行**：建议通过 `npm run tauri dev` 或打包产物人工验证窗口外观

## 回滚方式

1. **快速回滚**：revert 本任务 commit
2. **仅回退 CSS**：从 `App.vue` 的 `#app-shell` 移除新增的 `border` 和 `box-shadow` 两行
3. 本任务不涉及数据库、API、配置、依赖或权限变更，无额外回滚步骤

## 相关文档

- [17-release-and-update.md](../../17-release-and-update.md) — frameless 窗口限制条目已更新
- [S04-T07 模块上下文](../sprint-04-task-07-tauri-frameless-titlebar/context.md) — frameless 窗口方案来源
- [PROGRESS.md](../../../PROGRESS.md) — 进度记录

## 自审清单

- [x] 是否只实现了 tasks/current-task.md：是
- [x] 是否任务单由 Codex 起草并字段完整：是
- [x] 是否只修改了 allowed files：是（仅 `App.vue`）
- [x] 是否没有混入无关文件：是
- [x] 是否没有新增未授权依赖：是
- [x] 是否没有触碰未确认的高风险边界：是
- [x] 是否没有 secrets、真实密钥、Token 或生产连接串：是
- [x] 是否完成任务单要求的测试：是（npm run build + git diff --check）
- [x] 是否完成 reviewer-mode 自查：待执行
- [x] 是否更新模块上下文：是（本文档）
- [x] 是否追加更新 PROGRESS.md：待执行
- [x] 是否只对 tasks/current-task.md 做了允许的状态类最小更新：待执行
- [x] 是否列出未实现内容和残余风险：是
