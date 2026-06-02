# Sprint-04 内测 E2E Smoke Runbook

日期：2026-06-02
分支：`risk/sprint-04-e2e-smoke`
状态：`COMPLETED`（可复现）

## 背景

Sprint-04 closeout 记录了 12 项残余风险，其中"人工 GUI/E2E 验证缺口"（S04-T07 至 S04-T10 主要通过构建+编译+静态检查验证）是最适合优先压实的。本轮 E2E smoke 对可自动化验证的部分完整运行，对需人工 GUI 验证的部分提供可复现步骤。

## 环境信息

| 项目 | 值 |
|------|-----|
| OS | Windows 10 Pro 10.0.19045 |
| Python | 3.12.10 (D:\locaPath\Python312\python.exe) |
| Node.js | (Vite build 可用) |
| Rust | stable-x86_64-pc-windows-msvc |
| Tauri CLI | 2.x (via npm run tauri) |
| 工作目录 | D:\Project\ad-assistant |

## 验证结果汇总

### 自动化验证

| # | 验证项 | 命令 | 结果 | 耗时 |
|---|--------|------|------|------|
| A1 | 后端全量回归 | `pytest tests/ -v` | **PASS** — 293 passed, 74 skipped | ~43s |
| A2 | 桌面端构建 | `npm run build` | **PASS** — 74 modules, 0 errors | ~1s |
| A3 | Tauri release 打包 | `npm run tauri build` | **PASS** — EXE + MSI (2.8 MB) + NSIS (1.9 MB) 生成成功 | ~46s |
| A4 | 空白检查 | `git diff --check` | **PASS** — 无空白错误 | <1s |
| A5 | Tauri dev 编译 | `npm run tauri dev` | **BLOCKED_BY_ENV** — timeout 15s 在编译 124/355 crates 时终止（非编译错误，release build 已验证编译成功） | >15s |
| A6 | Git 状态 | `git status --short --branch` | **PASS** — 仅预期文件 | <1s |

### 代码静态验证

| # | 验证项 | 方法 | 结果 |
|---|--------|------|------|
| S1 | 后端 API 路由注册 | 审查 `cloud-backend/app/main.py` | **PASS** — dashboard, mock-ai, credits, plans, orders, admin, usage, provider-call-logs, auth, device 均已注册 |
| S2 | 桌面端路由表 | 审查 `desktop-app/src/router.ts` | **PASS** — `/` (Dashboard), `/ocr`, `/ai-ad-copy`, `/membership`, `/history`, `/login` |
| S3 | Sidebar 导航 | 审查 `AppSidebar.vue` | **PASS** — AI 文案生成 (/ai-ad-copy)、OCR 识别 (/ocr)、会员中心 (/membership)、使用日志 (/history) 均已启用 |
| S4 | 快捷入口 | 审查 `DashboardPage.vue` + `QuickEntryCard.vue` + `dashboardMock.ts` | **PASS** — AI 文案生成 和 OCR 已启用，其余标记 "即将开放" |
| S5 | Tauri capabilities | 审查 `capabilities/default.json` | **PASS** — 仅 core:window 7 项权限 |
| S6 | Frameless 窗口配置 | 审查 `tauri.conf.json` | **PASS** — decorations: false, backgroundColor: "#07111f" |
| S7 | 自定义标题栏 | 审查 `AppTopbar.vue` | **PASS** — data-tauri-drag-region + 最小化/最大化/关闭按钮 |

### 打包产物验证

| # | 验证项 | 产物路径 | 结果 |
|---|--------|---------|------|
| P1 | MSI 安装包 | `src-tauri/target/release/bundle/msi/AdAssistant_0.1.0_x64_en-US.msi` | **PASS** — 2.8 MB |
| P2 | NSIS 安装包 | `src-tauri/target/release/bundle/nsis/AdAssistant_0.1.0_x64-setup.exe` | **PASS** — 1.9 MB |
| P3 | 裸 EXE | `src-tauri/target/release/ad-assistant-desktop.exe` | **PASS** — release 编译成功 |
| P4 | 代码签名 | — | **NOT_RUN** — 无签名证书（已知残余风险） |
| P5 | NSIS 离线稳定性 | — | **NOT_RUN** — 本次 NSIS 下载成功，但历史上有超时记录 |

## 核心链路验证

以下链路需要后端 + 本地 OCR 服务 + 桌面端 Tauri 窗口协同运行。本轮因环境限制（当前终端无 GUI 显示），部分项目标记为 `NOT_RUN` 并附带手动复现步骤。

### L1: 登录/设备绑定

- **状态**: `NOT_RUN`（需 GUI + 运行后端）
- **依赖**: cloud-backend 运行中 + 桌面端 Tauri dev/build 启动
- **手动复现步骤**:
  1. 启动后端: `cd ad-assistant/cloud-backend && uvicorn app.main:app --reload`
  2. 启动桌面: `cd ad-assistant/desktop-app && npm run tauri dev`
  3. 输入测试用户凭证，点击登录
  4. 验证: 自动跳转到 Dashboard
- **代码级验证**: LoginPage.vue 使用 `crypto.randomUUID()` 生成 device fingerprint + localStorage 持久化 (S03-T01)；authStore token 为 Pinia 内存存储

### L2: Dashboard 数据加载

- **状态**: `NOT_RUN`（需运行后端 + 登录态）
- **依赖**: cloud-backend + 有效 auth token
- **手动复现步骤**:
  1. 登录后观察 Dashboard stats 卡片和最近订单表
  2. 如后端不可用，应显示 mock fallback + loading 骨架
- **代码级验证**: DashboardPage.vue 调用 `GET /api/v1/dashboard/summary`（S04-T02），有 mock fallback 逻辑；后端 dashboard_service.py 聚合 stats + recent orders

### L3: OCR 上传、结果展示、历史记录

- **状态**: `NOT_RUN`（需本地 OCR 服务 + GUI）
- **依赖**: local-service 运行 + PaddleOCR
- **手动复现步骤**:
  1. 启动本地 OCR 服务
  2. 桌面端进入 OCR 页面 (`/ocr`)
  3. 上传图片，验证 OCR 结果展示
  4. 切换到历史记录页 (`/history`)，验证历史列表
- **代码级验证**: OcrPage.vue 调用 `POST /local/ocr`；ocrService.ts 调用本地 FastAPI 端点；后端测试 42 passed (S04-T03)

### L4: AI 文案生成

- **状态**: `NOT_RUN`（需运行后端 + 登录态，DeepSeek API key 需配置）
- **依赖**: cloud-backend + DeepSeek API key（或自动降级到 MockProvider）
- **手动复现步骤**:
  1. 登录后进入 AI 文案生成页面 (`/ai-ad-copy`)
  2. 填写文案参数表单，提交
  3. 观察结果（真实 AI 文案 或 Mock 回退）
- **代码级验证**: AdCopyPage.vue 调用 `POST /api/v1/mock-ai/ad-copy`；Provider 降级链 deepseek→mock（S04-T01）；后端 test_deepseek_provider.py 25 passed + test_provider_reliability.py 29 passed

### L5: 会员/套餐/充值记录

- **状态**: `NOT_RUN`（需运行后端 + 登录态）
- **依赖**: cloud-backend
- **手动复现步骤**:
  1. 进入会员中心 (`/membership`)
  2. 验证套餐展示（3 列对比）
  3. 选择套餐 → 确认充值 → 检查记录
- **代码级验证**: MembershipPage.vue 已实现；后端 test_plans + test_recharge + test_admin_grant 29 passed

### L6: OCR 历史删除/清空

- **状态**: `NOT_RUN`（需本地 OCR 服务 + 有历史数据）
- **依赖**: local-service + SQLite OCR 历史
- **手动复现步骤**:
  1. 进入历史记录页 (`/history`)
  2. 点击单条删除 → 确认弹窗
  3. 点击清空全部 → 确认弹窗
- **代码级验证**: HistoryPage.vue 已实现；后端 test_ocr_history.py 19 passed + test_ocr_api.py 23 passed (S04-T03)

### L7: Tauri 窗口操作

- **状态**: `NOT_RUN`（需 GUI + Tauri 窗口）
- **依赖**: Tauri 桌面应用启动
- **手动复现步骤**:
  1. 启动 `npm run tauri dev` 或直接运行打包 EXE
  2. 拖拽标题栏移动窗口
  3. 点击最小化、最大化、还原、关闭按钮
  4. 验证 frameless 窗口无系统标题栏
  5. 观察 CSS 内描边 + 内阴影效果
  6. 验证最大化状态无异常边距/裁切
- **代码级验证**: AppTopbar.vue 窗口控制按钮通过 `@tauri-apps/api/window` 调用；App.vue `#app-shell` CSS 视觉边界（S04-T10）

### L8: 打包产物安装 Smoke

- **状态**: `NOT_RUN`（需人工在 Windows 桌面执行）
- **依赖**: MSI/NSIS 安装包
- **手动复现步骤**:
  1. 双击 `AdAssistant_0.1.0_x64_en-US.msi` → 安装
  2. 或双击 `AdAssistant_0.1.0_x64-setup.exe` → 安装
  3. 从开始菜单或桌面快捷方式启动
  4. 注意: Windows SmartScreen 会弹出"Windows protected your PC"警告（未签名，已知风险）
  5. 验证应用窗口正常显示、深色主题、品牌图标

## 运行命令参考

### 自动化命令（已验证通过）

```powershell
# 后端全量回归
cd ad-assistant/cloud-backend
python -m pytest tests/ -v

# 桌面端构建
cd ad-assistant/desktop-app
npm run build

# Tauri 打包（需网络下载 NSIS）
cd ad-assistant/desktop-app
npm run tauri build

# 空白检查
git diff --check
```

### 手动验证命令（需 GUI 环境）

```powershell
# 启动后端（终端 1）
cd ad-assistant/cloud-backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 启动本地 OCR 服务（终端 2）
cd ad-assistant/desktop-app/local-service
python main.py

# 启动 Tauri 桌面端（终端 3）
cd ad-assistant/desktop-app
npm run tauri dev

# 或浏览器模式（无需 Tauri）
cd ad-assistant/desktop-app
npm run dev
```

## 已知阻塞项

| # | 阻塞项 | 影响 | 后续建议 |
|---|--------|------|---------|
| B1 | 无 GUI 显示环境 | L1-L8 所有 GUI 链路无法自动化 | 用户在 Windows 桌面按 runbook 手动执行 |
| B2 | 后端未运行 | L1/L2/L4/L5 需后端 API | 启动 uvicorn 后手动验证 |
| B3 | 本地 OCR 服务未运行 | L3/L6 需本地 OCR 服务 | 启动 local-service 后手动验证 |
| B4 | DeepSeek API Key 未配置 | L4 需真实 AI 调用（可降级到 Mock） | 配置 `.env` 或依赖 Provider 降级链 |
| B5 | Tauri dev 首次编译慢 | A5 timeout 15s 不够 | 不设 timeout，等待编译完成（release build 已验证） |
| B6 | 未签名安装包 | P4 SmartScreen 警告 | 需代码签名证书（Sprint-05 候选） |

## 残余风险状态更新

基于本次 E2E smoke 结果，Sprint-04 残余风险状态如下：

| # | 残余风险 | E2E 后状态 | 说明 |
|---|---------|-----------|------|
| 1 | 未签名安装包 | **仍待修复** | 无签名证书，SmartScreen 警告（Sprint-05 候选） |
| 2 | NSIS 下载网络不稳定 | **已缓解** | 本次 build NSIS 下载成功；历史有超时，建议预缓存 |
| 3 | 正式品牌 VI 未确认 | **仍待确认** | 内测图标可用，正式品牌待用户决策 |
| 4 | CSS 窗口阴影 ≠ 原生 DWM | **仍待专项** | CSS 方案可用但层次感有限，原生方案需专项任务 |
| 5 | 模拟支付无风控 | **仍待修复** | 当前为 simulated，无风控/限额（Sprint-05 候选） |
| 6 | 管理员白名单无 RBAC | **仍待修复** | 硬编码 ADMIN_USER_IDS（Sprint-05 候选） |
| 7 | 后台管理能力不足 | **仍待修复** | 无管理 UI/报表/监控（Sprint-05 候选） |
| 8 | Tauri 权限最小化 | **已压实** | 仅 core:window 7 项，当前功能足够 |
| 9 | 人工 GUI/E2E 验证缺口 | **部分压实** | 自动化部分全覆盖；GUI 部分有 runbook 步骤但未执行 |
| 10 | 月度积分发放调度器未实现 | **仍待修复** | 需 cron/后台任务（Sprint-05 候选） |
| 11 | Provider 无熔断器/健康检查 | **仍待修复** | 降级为静态 1 级链（Sprint-05 候选） |
| 12 | 余额不足 402 UX | **仍待优化** | 402 错误已正确返回（S04-T01 验证），桌面端充值引导未实现 |

## 新发现或环境阻塞

- **B5 (Tauri dev 首次编译慢)**: debug 模式编译 355 crates 耗时 >15s，但 release build 已成功（`npm run tauri build`），证明编译链完整可用。
- 无新发现阻塞性缺陷。

## 总结

| 指标 | 值 |
|------|-----|
| 自动化 PASS | 5/6（A1-A4, A6；A5 BLOCKED_BY_ENV） |
| 代码静态验证 PASS | 7/7 |
| 打包产物 PASS | 3/5（P4-P5 NOT_RUN） |
| GUI 链路 NOT_RUN | 8/8（L1-L8 需 GUI 环境） |
| 残余风险已压实/缓解 | 2/12（Tauri 权限 + NSIS 网络） |
| 残余风险仍待修复 | 9/12 |
| 残余风险部分压实 | 1/12（GUI 缺口 → 有 runbook 未执行） |
| 新发现缺陷 | 0 |
