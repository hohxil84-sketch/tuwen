# S04-T05: 桌面端快捷入口接入已有真实功能

## 状态

`IMPLEMENTED_SELF_REVIEW_PASSED`

## 分支

`feature/sprint-04-task-05-shortcut-entry-wiring`

## 实现记录 (2026-06-02)

### 修改文件

- `desktop-app/src/components/dashboard/AppSidebar.vue` — 核心功能中 `AI 文案生成` 从 `disabled: true, route: "/"` 改为 `disabled: false, route: "/ai-ad-copy"`（仅改一行）
- `docs/module-context/sprint-04-task-05-shortcut-entry-wiring/context.md`（新增）— 入口映射表、路由清单、未实现功能、扩展点
- `PROGRESS.md` — 追加本任务进度记录
- `tasks/current-task.md` — 本记录

### 已验证无需修改的文件

- `desktop-app/src/components/dashboard/QuickEntryCard.vue` — disabled 样式（opacity: 0.56, cursor: not-allowed, hover 禁用, "即将开放" badge）已足够清晰，无需调整
- `desktop-app/src/pages/dashboardMock.ts` — MOCK_QUICK_ENTRIES 中 AI 文案生成已有正确 route `/ai-ad-copy` 且无 disabled 标志，OCR 已有正确 route `/ocr`
- `desktop-app/src/pages/DashboardPage.vue` — 快捷入口使用 MOCK_QUICK_ENTRIES，无需修改
- `desktop-app/src/router.ts` — 所有必需路由（/ai-ad-copy, /ocr, /membership, /history）已存在，无需修改

### 实现内容

全部按计划完成。核心改动：
- Sidebar `AI 文案生成` 从 disabled 占位改为可点击，跳转 `/ai-ad-copy`
- 其他已实现功能入口（OCR、会员中心、使用日志）确认均可正常跳转
- Dashboard 快捷入口 AI 文案生成和 OCR 确认已正确配置
- 未实现功能保持 disabled + "即将开放"
- 不新增会员中心快捷入口（保持 6 宫格布局不变），Sidebar 入口已确保可用

### 未实现内容

无——计划内全部完成。

### 自审结论

- 只实现了 tasks/current-task.md 允许的内容: 是
- 只修改了 allowed files: 是
- 未混入无关文件: 是
- 未新增依赖: 是
- 未触碰高风险边界: 是
- 未存储 secrets: 是
- 构建: npm run build 通过（68 modules, 0 errors）
- PROGRESS.md: 已更新
- 模块上下文: 已创建

### 测试结果

```
# 前端构建
npm run build
68 modules, 0 errors

# diff 检查
git diff --check
通过
```

### 是否触发高风险暂停规则

否——本任务仅修改一行前端入口映射和文档记录，不涉及任何高风险边界。

### 风险和回滚方式

1. **残余风险**: 无。改动仅一行代码，只将已有的 AI 文案页面路由正确接入 Sidebar。
2. **回滚方式**: revert 本任务 commit，或在 `AppSidebar.vue` 中恢复 `AI 文案生成` 为 `disabled: true, route: "/"`。

---

## 背景

Sprint-03 已完成桌面端 Dashboard UI 壳，Sprint-04 Task-02 已完成 Dashboard summary API 接入和 AI 文案生成页面，Sprint-04 Task-03 已完成 OCR 历史删除/清空，Sprint-04 Task-04 已完成会员中心、套餐、充值和订单记录。

当前 Dashboard 和 Sidebar 里仍有部分入口处于 disabled 或占位状态。按 `PROGRESS.md` 最新记录，S04-T04 后续任务是 `S04-T05（快捷入口接入真实功能）`。

本任务只把已经存在的页面和已有功能接到桌面端快捷入口与侧边栏，不开发新的业务能力。

## 用户目标

按当前项目进度，把桌面端首页和侧边栏里已经具备后端或页面基础的功能入口接起来，让 CC 能从工作台直接进入已有真实功能；暂未实现的功能继续明确显示“即将开放”，不能误导用户。

Codex 保守拆解结论：

- 本次只做前端入口接线和状态文案。
- 可接入的已有功能：AI 文案生成、OCR 文字识别、会员中心、OCR 历史/使用日志。
- 不接入尚未实现的 AI 效果图生成、图片改尺寸、图片转 SVG、印刷检查、智能抠图、证件照、批量处理、拼版、素材库、模板中心、客户管理、软件设置、更新检查。

## 本次只开发什么

- 修正 Sidebar 核心功能入口：
  - `AI 文案生成` 必须可点击并跳转 `/ai-ad-copy`。
  - `OCR 文字识别` 保持可点击并跳转 `/ocr`。
  - `会员中心` 保持可点击并跳转 `/membership`。
  - `使用日志` 保持可点击并跳转 `/history`。
  - 未实现功能继续 disabled，并显示“即将开放”。
- 修正 Dashboard 快捷入口：
  - `AI 文案生成` 必须可点击并跳转 `/ai-ad-copy`。
  - `OCR` 必须可点击并跳转 `/ocr`。
  - 如果新增 `会员中心` 快捷入口，必须跳转 `/membership`，且不能破坏现有 6 宫格整体视觉；如不新增，则至少保证 Sidebar 入口可用。
  - 未实现快捷入口必须保持 disabled，并通过视觉和文案明确“即将开放”。
- 修正入口文案：
  - 已可用入口不要显示“即将开放”。
  - 未实现入口不要显示成已可用、在线、已接入或真实生成能力。
- 必要时调整 `QuickEntryCard.vue` 的 disabled 展示，让禁用入口有清晰不可点击状态。
- 必要时更新 `docs/module-context/sprint-04-task-05-shortcut-entry-wiring/context.md`，记录本任务入口映射、未实现功能和后续扩展点。
- 完成后追加更新 `PROGRESS.md`，记录实现范围、测试、风险和回滚方式。

## 本次不开发什么

- 不开发 AI 效果图生成。
- 不开发图片改尺寸、DPI、裁切。
- 不开发图片转 SVG、印刷检查、智能抠图、证件照、批量处理、拼版、素材库、模板中心、客户管理、软件设置或更新检查。
- 不新增后端 API。
- 不修改数据库、DDL、migration、模型、credit、payment、provider、auth、Tauri 权限或本地 OCR 服务。
- 不接入真实 AI 图片 Provider。
- 不接入真实支付。
- 不新增依赖。
- 不改 package/lockfile。
- 不重构 Dashboard 布局和视觉系统。

## 允许修改哪些文件

- `desktop-app/src/components/dashboard/AppSidebar.vue`
- `desktop-app/src/components/dashboard/QuickEntryCard.vue`
- `desktop-app/src/pages/dashboardMock.ts`
- `desktop-app/src/pages/DashboardPage.vue`
- `docs/module-context/sprint-04-task-05-shortcut-entry-wiring/context.md`（可新增）
- `PROGRESS.md`
- `tasks/current-task.md`

## 禁止修改哪些文件

- `cloud-backend/**`
- `shared/**`
- `desktop-app/src-tauri/**`
- `desktop-app/local-service/**`
- `desktop-app/package.json`
- `desktop-app/package-lock.json`
- `package.json`
- `package-lock.json`
- `desktop-app/src/router.ts`，除非发现现有路由缺失且必须补齐；如需修改，先在交付说明中说明原因
- 数据库文件、日志、构建产物、本地缓存和生成物

## 本地环境和服务规则

- 本任务是前端入口接线，默认不需要启动数据库、Redis、Docker 或本地 OCR 服务。
- 如需本地启动前端，只运行本机 Node/npm。
- 不默认使用 Docker；只有用户明确批准 Docker fallback 时才允许。

## 注释语言要求

- CC 新增或修改代码注释时必须使用中文。
- 第三方协议、外部 API 固定术语、错误码、英文专有名词和工具原始输出除外。

## 是否允许新增依赖

不允许。

## 是否涉及重大变更

否。

本任务只修改桌面端已有入口映射和文档记录，不涉及数据库、API contract、Provider、Auth、Credit、Payment、Tauri 权限、CI 或依赖。

## 高风险边界

本任务不得触碰以下高风险边界：

- 数据库 schema / DDL / migration
- API / OpenAPI / shared DTO
- Auth / Token / 权限
- Provider / credit / payment / provider cost
- Tauri permissions
- dependencies / lockfiles
- CI / workflows / deployment
- filesystem permissions
- 删除文件、重命名目录、大规模重构

如果实现过程中发现必须触碰以上任一边界，CC 必须暂停并请求 Codex/用户更新任务单。

## 验收标准

- [ ] Sidebar 中 `AI 文案生成` 可点击，并跳转 `/ai-ad-copy`。
- [ ] Sidebar 中 `OCR 文字识别` 可点击，并跳转 `/ocr`。
- [ ] Sidebar 中 `会员中心` 可点击，并跳转 `/membership`。
- [ ] Sidebar 中 `使用日志` 可点击，并跳转 `/history`。
- [ ] Dashboard 快捷入口中 `AI 文案生成` 可点击，并跳转 `/ai-ad-copy`。
- [ ] Dashboard 快捷入口中 `OCR` 可点击，并跳转 `/ocr`。
- [ ] 未实现功能仍然 disabled，不会跳转到错误页面，也不会显示成已接入真实功能。
- [ ] 禁用入口视觉上明确不可点击，并显示“即将开放”或等价中文说明。
- [ ] 不破坏 Dashboard 当前大窗口/小窗口布局，不引入横向滚动条或整体缩放回归。
- [ ] 登录、OCR、历史、AI 文案、会员中心页面仍可通过路由访问。
- [ ] 没有修改后端、数据库、shared DTO、Tauri、依赖或 lockfile。

## 测试方式

必须运行：

```powershell
cd ad-assistant/desktop-app
npm run build
```

必须运行：

```powershell
git diff --check
```

建议人工验证：

- 打开桌面端开发页面或构建后的前端页面。
- 点击 Sidebar：AI 文案生成、OCR 文字识别、会员中心、使用日志。
- 点击 Dashboard 快捷入口：AI 文案生成、OCR。
- 确认未实现入口不可点击或点击无跳转，并显示“即将开放”。
- 缩小窗口，确认 Dashboard 没有出现不可接受的滚动条或布局错位。

如果无法启动前端页面，CC 必须说明原因，并至少提供 `npm run build` 和代码级路由映射检查结果。

## 安全检查

- 不下发 API Key 到客户端。
- 不由客户端扣点。
- 不由客户端决定套餐。
- 不绕过云端授权。
- 不明文保存 Token。
- 不新增真实 AI Provider 调用。
- 不新增支付、充值到账或管理员赠送逻辑。
- 不记录用户隐私数据。

## 回滚方案

- revert 本任务 commit 即可恢复入口映射和文档记录。
- 如果只改了前端入口配置，可恢复 `AppSidebar.vue`、`dashboardMock.ts`、`QuickEntryCard.vue`、`DashboardPage.vue` 到任务前版本。
- 本任务不涉及数据库迁移和数据回滚。

## CC 必须暂停的情况

- 需要修改 `Allowed Files` 之外的文件，且不是现有路由缺失导致的必要补齐。
- 需要改后端 API、数据库、shared DTO、Provider、Auth、Credit、Payment、Tauri 权限、依赖或 CI。
- 发现 `/ai-ad-copy`、`/ocr`、`/membership`、`/history` 任一路由不存在且无法在当前允许范围内确认。
- 需要删除文件、重命名目录或做大规模重构。
- `npm run build` 失败且修复超出当前入口接线范围。
- 发现 secrets、真实密钥、生产连接串或用户敏感数据泄露风险。
- 需要 Docker 但未获用户明确批准。

## 完成输出要求

执行者完成后必须用中文输出：

- 修改文件列表
- 实现内容
- 未实现内容
- 测试命令和结果
- 人工验证结果或未验证原因
- 自审结论
- reviewer-mode 自查结果
- 风险点
- 回滚方式
- 是否触发重大变更
- 是否更新模块上下文
- 是否更新 `PROGRESS.md`
- 中文 commit message
- PR title/body 中文摘要
- 合并后的中文交付说明，包括用户确认来源、PR 编号、合并方式和合并结果
