# S04-T05: 桌面端快捷入口接入已有真实功能 — 模块上下文

## 概述

本任务将桌面端 Dashboard 和 Sidebar 中已存在页面基础的快捷入口从 disabled 占位状态改为可点击跳转，并对尚未实现的功能明确保留"即将开放"禁用状态。

## 入口映射

### Sidebar 核心功能

| 入口 | 路由 | 状态 | 说明 |
|------|------|------|------|
| AI 效果图生成 | `/` | disabled | 未实现，显示"即将开放" |
| AI 文案生成 | `/ai-ad-copy` | **enabled** | 跳转 AdCopyPage（S04-T02） |
| 图片改尺寸 | `/` | disabled | 未实现 |
| 图片转矢量 SVG | `/` | disabled | 未实现 |
| 印刷检查 | `/` | disabled | 未实现 |
| OCR 文字识别 | `/ocr` | enabled | 跳转 OcrPage（Sprint-03） |

### Sidebar 其他分组

| 入口 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 会员中心 | `/membership` | enabled | 跳转 MembershipPage（S04-T04） |
| 我的订单 | `/history` | enabled | 跳转 HistoryPage |
| 使用日志 | `/history` | enabled | 跳转 HistoryPage |
| 客户管理 | — | disabled | 未实现 |
| 软件设置 | — | disabled | 未实现 |
| 更新检查 | — | disabled | 未实现 |

### Dashboard 快捷入口（6 宫格）

| 入口 | 路由 | 状态 | 说明 |
|------|------|------|------|
| AI 效果图生成 | — | disabled | 未实现 |
| AI 文案生成 | `/ai-ad-copy` | **enabled** | 无 disabled 标志，跳转正常 |
| 图片改尺寸 | — | disabled | 未实现 |
| 图片转 SVG | — | disabled | 未实现 |
| 印刷检查 | — | disabled | 未实现 |
| OCR | `/ocr` | enabled | 跳转 OcrPage |

## 关键文件

- `desktop-app/src/components/dashboard/AppSidebar.vue` — Sidebar 导航，包含 `coreFeatures` 数组和路由映射
- `desktop-app/src/components/dashboard/QuickEntryCard.vue` — 快捷入口卡片，包含 disabled 展示和跳转逻辑
- `desktop-app/src/pages/dashboardMock.ts` — Dashboard mock 数据，包含 `MOCK_QUICK_ENTRIES`
- `desktop-app/src/pages/DashboardPage.vue` — Dashboard 主页面
- `desktop-app/src/router.ts` — 路由配置，定义所有已实现页面的路径映射

## 路由清单（已实现页面）

| 路径 | 名称 | 组件 |
|------|------|------|
| `/` | dashboard | DashboardPage.vue |
| `/login` | login | LoginPage.vue |
| `/ocr` | ocr | OcrPage.vue |
| `/history` | history | HistoryPage.vue |
| `/ai-ad-copy` | ai-ad-copy | AdCopyPage.vue |
| `/membership` | membership | MembershipPage.vue |

## 未实现功能（保持 disabled）

- AI 效果图生成
- 图片改尺寸 / DPI / 裁切
- 图片转 SVG
- 印刷检查
- 智能抠图
- AI 证件照
- 批量处理
- 拼版助手
- 素材库
- 模板中心
- 客户管理
- 软件设置
- 更新检查

## 扩展点

- 当对应功能实现后，仅需修改 `AppSidebar.vue` 中的 `coreFeatures` 数组或 `dashboardMock.ts` 中的 `MOCK_QUICK_ENTRIES`，将 `disabled: true` 改为 `disabled: false` 并设置正确的 `route`。
- Dashboard 快捷入口支持 6 宫格布局。如果未来需要新增第 7 个已实现入口，可考虑替换某个 disabled 入口或调整网格布局（需单独任务评估）。

## 设计约束

- 不改后端 API
- 不改 shared DTO
- 不改 Tauri 权限
- 不新增依赖
- Dashboard 6 宫格布局不变
- disabled 入口统一显示"即将开放"
