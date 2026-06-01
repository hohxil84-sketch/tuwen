# 26 桌面端首页 UI 改版执行说明

## 目标

桌面端首页先做成一个可运行、可演示、视觉完整的深色 SaaS 工作台。

本阶段只实现前端界面，不接真实后端能力，不改数据库，不引入 Docker，不实现真实 AI 调用。后续再按模块把 OCR、AI 效果图生成、AI 文案生成、订单、素材库等功能逐步接入。

参考方向是用户提供的深色桌面工作台截图：左侧功能导航、顶部状态栏、主区域欢迎卡片、统计卡片、快捷入口、最近订单、最近生成图、底部连接状态。

## 设计原则

### 先做 UI 壳

第一阶段的核心目标是“看起来就是成品”，而不是把所有业务一次性接完。

要求：

- 所有首页数据先使用前端 mock 数据。
- 首页不依赖云端接口、本地服务、数据库或缓存。
- 离线启动前端也能完整看到首页。
- 点击功能入口可以跳转到已有页面，或者进入明确标注的占位状态。
- 不因为 UI 改版破坏已有登录、OCR、历史记录页面。

### 做生产工具，不做营销页

首页应该像一线操作员每天使用的生产工具，而不是官网落地页。

应该强调：

- 功能入口清晰。
- 状态信息清晰。
- 可用次数、订单、任务、生成记录一眼可见。
- 操作路径短。

避免：

- 大面积营销 Hero。
- 抽象口号占据主屏。
- 聊天机器人式主入口。
- 隐藏授权、余额、到期时间、连接状态。

### 保留后续扩展空间

当前只是静态 UI，但结构要为后续功能接入预留位置。

建议把 mock 数据集中放在页面顶部或独立 mock 文件中，后续替换为接口数据时不要重写页面结构。

## 页面信息架构

桌面端主界面建议采用固定外壳：

- 左侧导航栏。
- 顶部状态栏。
- 中间主内容区。
- 底部状态栏。

整体布局：

```text
+--------------------------------------------------------------+
| 顶部状态栏：应用名 / 用户 / 会员 / 在线状态 / 设置           |
+------------+-------------------------------------------------+
|            | 欢迎卡片                  | 数据统计卡片组       |
| 左侧导航栏 |-------------------------------------------------|
|            | 快捷入口 6 个功能卡片                         |
|            |-------------------------------------------------|
|            | 最近订单表格              | 最近生成效果图       |
+------------+-------------------------------------------------+
| 底部状态栏：连接状态 / 版本 / 检查更新                       |
+--------------------------------------------------------------+
```

推荐最小窗口宽度按 `1280px` 设计。宽度不足时优先压缩内容区卡片间距，不要让左侧导航和顶部栏错位。

## 左侧导航栏

### 视觉要求

左侧导航栏是整个桌面工作台的主轴。

建议：

- 宽度：`232px` 到 `256px`。
- 背景：深蓝黑，例如 `#07111f`、`#0b1626`。
- 右侧边框：半透明蓝灰色，例如 `rgba(148, 163, 184, 0.14)`。
- 当前菜单：蓝色渐变高亮，例如 `linear-gradient(135deg, #1d4ed8, #2563eb)`。
- 菜单项高度：`40px` 到 `44px`。
- 菜单项圆角：`8px` 到 `10px`。
- 图标和文字水平排列。

### 导航分组

建议分组如下：

```text
工作台

核心功能
- AI 效果图生成
- AI 文案生成
- 图片改尺寸
- 图片转矢量 SVG
- 印刷检查
- OCR 文字识别

辅助功能
- 智能抠图
- AI 证件照
- 批量处理
- 拼版助手
- 素材库
- 模板中心

订单管理
- 我的订单
- 客户管理

系统设置
- 软件设置
- 更新检查
- 使用日志
```

当前已有 OCR 页面和历史记录页面，首版可以这样映射：

| 菜单 | 当前行为 |
| --- | --- |
| 工作台 | 进入新首页 |
| OCR 文字识别 | 跳转 `/ocr` |
| 我的订单 | 暂时显示 mock 区域或跳转 `/history` |
| 使用日志 | 暂时跳转 `/history` |
| 其他功能 | 显示“即将开放”或停留在首页 |

## 顶部状态栏

### 内容

顶部状态栏用于显示当前账号和运行状态。

建议包含：

- 应用 Logo：`AI 图文广告助手`。
- 版本号：例如 `v1.0.0`。
- 用户信息：头像、昵称、版本等级。
- 会员到期时间：例如 `2025-12-31`。
- 在线状态：云朵图标或圆点 + `在线`。
- 设置入口：齿轮图标。

### 视觉要求

- 高度：`56px` 到 `64px`。
- 背景和左侧导航保持同一深色体系。
- 底部边框：细线分隔。
- 用户、会员、在线状态之间使用细竖线或间距分隔。
- 到期时间、在线状态不要做成强按钮，避免抢主操作视觉。

## 主内容区

主内容区建议使用 `CSS Grid`。

推荐结构：

```text
main.dashboard-main
  section.top-row
    welcome-card
    stats-card-group
  section.quick-entry-panel
    quick-entry-card * 6
  section.bottom-row
    recent-orders-card
    recent-images-card
```

### 欢迎卡片

内容示例：

```text
晚上好，张老板！
AI 图文广告助手已为您准备好，今天也要加油接单哦！
```

要求：

- 占据顶部左侧较大面积。
- 使用深蓝渐变背景。
- 标题字号明显大于正文。
- 可以保留一个轻量 emoji 或图形点缀，但不要过度卡通。

### 数据统计卡片

建议 4 个统计项：

| 指标 | 示例值 | 辅助信息 |
| --- | --- | --- |
| 今日使用次数 | `23 / 500` | 剩余额度 `477` |
| 本月订单 | `18` | 较上月 `+12%` |
| 生成图片 | `56` | 较昨日 `+8` |
| 会员等级 | `高级版` | 到期 `2025-12-31` |

要求：

- 统计项放在同一个横向卡片组内。
- 每个统计项左侧使用彩色图标容器。
- 数字要大，辅助文字要弱化。
- 增长信息使用绿色或红色，但不要大面积使用。

### 快捷入口

建议 6 个快捷入口：

| 功能 | 标题 | 描述 | 色彩方向 |
| --- | --- | --- | --- |
| AI 效果图生成 | AI 效果图生成 | 输入描述，生成效果图 | 蓝紫 |
| AI 文案生成 | AI 文案生成 | 生成广告语、店名等 | 橙色 |
| 图片改尺寸 | 图片改尺寸 | 修改尺寸、DPI、裁切等 | 青色 |
| 图片转 SVG | 图片转 SVG | 位图转矢量图 | 蓝色 |
| 印刷检查 | 印刷检查 | 检查文件是否适合印刷 | 绿色 |
| OCR | OCR | 识别图片/PDF 文字 | 紫色 |

卡片要求：

- 每张卡片独立可点击。
- 图标容器尺寸约 `64px` 到 `76px`。
- 标题清晰，描述短。
- hover 时可以轻微上浮或加亮边框。
- OCR 卡片应该能进入现有 `/ocr` 页面。

### 最近订单

最近订单先使用 mock 表格。

字段建议：

- 订单号。
- 客户名称。
- 项目名称。
- 状态。
- 更新时间。

mock 数据示例：

| 订单号 | 客户名称 | 项目名称 | 状态 | 更新时间 |
| --- | --- | --- | --- | --- |
| DD2024052001 | 宠物医院-小李 | 门头设计 | 已完成 | 2024-05-20 20:30 |
| DD2024052002 | 奶茶店-王老板 | 灯箱设计 | 进行中 | 2024-05-20 19:15 |
| DD2024052003 | 超市-张姐 | 宣传单页 | 已完成 | 2024-05-20 18:50 |
| DD2024052004 | 理发店-小陈 | 价目表设计 | 待确认 | 2024-05-20 17:20 |
| DD2024052005 | 烧烤店-老周 | 门头+灯箱 | 进行中 | 2024-05-20 16:10 |

状态标签建议：

- 已完成：绿色。
- 进行中：蓝色。
- 待确认：橙色。
- 失败或异常：红色，首版可不放。

### 最近生成效果图

最近生成效果图先使用本地 mock 图片或渐变占位图。

建议 6 个卡片，标题和时间如下：

- 宠物医院门头设计，`2024-05-20 20:30`。
- 奶茶店灯箱设计，`2024-05-20 19:15`。
- 烧烤店门头设计，`2024-05-20 18:22`。
- 美甲店装修效果图，`2024-05-20 17:45`。
- 超市招牌设计，`2024-05-20 16:50`。
- 健身房门头设计，`2024-05-20 15:30`。

如果暂时没有合适图片，不要使用空白灰块。可以用 CSS 渐变背景 + 店铺名称文字模拟广告图，保证视觉完整。

## 底部状态栏

底部状态栏建议包含：

- 左侧：绿色圆点 + `已连接到服务器`。
- 中间：`版本：1.0.0`。
- 右侧：`检查更新`。

当前阶段不需要真的检测服务器连接，文案可以是 mock 状态。但必须避免误导成真实联网结果，可以在代码注释或 mock 数据命名中标注。

## 视觉规范

### 色彩

建议使用 CSS 变量集中管理：

```css
:root {
  --bg-app: #07111f;
  --bg-sidebar: #081322;
  --bg-panel: #101d31;
  --bg-panel-soft: #13233a;
  --border-subtle: rgba(148, 163, 184, 0.14);
  --border-active: rgba(59, 130, 246, 0.55);
  --text-main: #e5edf7;
  --text-muted: #94a3b8;
  --text-soft: #64748b;
  --blue: #3b82f6;
  --blue-strong: #2563eb;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --purple: #8b5cf6;
  --cyan: #06b6d4;
}
```

### 字体

在现有项目无额外字体资源时，先使用系统中文字体即可，不要为了 UI 改版引入远程字体。

建议：

```css
font-family:
  "Microsoft YaHei",
  "PingFang SC",
  "Noto Sans SC",
  system-ui,
  sans-serif;
```

### 间距

建议：

- 页面外边距：`16px` 到 `20px`。
- 卡片内边距：`20px` 到 `28px`。
- 卡片间距：`16px`。
- 分组标题和内容间距：`12px`。

### 卡片

通用卡片建议：

```css
.dashboard-card {
  background: linear-gradient(180deg, rgba(19, 35, 58, 0.96), rgba(13, 27, 45, 0.96));
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 12px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
}
```

### 动效

只做少量有意义的动效：

- 页面加载时内容轻微上浮淡入。
- 快捷入口 hover 时上浮 `2px` 到 `4px`。
- 当前导航高亮有颜色过渡。

避免：

- 大量循环动画。
- 粒子背景。
- 强烈闪烁。
- 影响桌面端性能的复杂滤镜。

## 建议文件拆分

当前桌面端是 Vue 3 + Vite + Vue Router + Pinia。

建议 CC 按以下方式实现：

```text
desktop-app/src/App.vue
desktop-app/src/router.ts
desktop-app/src/pages/DashboardPage.vue
desktop-app/src/components/dashboard/AppSidebar.vue
desktop-app/src/components/dashboard/AppTopbar.vue
desktop-app/src/components/dashboard/DashboardStatCard.vue
desktop-app/src/components/dashboard/QuickEntryCard.vue
desktop-app/src/components/dashboard/RecentOrders.vue
desktop-app/src/components/dashboard/RecentGeneratedImages.vue
```

首版也可以少拆组件，但不要把所有逻辑长期堆在 `App.vue` 里。

推荐职责：

| 文件 | 职责 |
| --- | --- |
| `App.vue` | 只负责桌面外壳和 `router-view`，不要写大量业务卡片 |
| `DashboardPage.vue` | 首页主内容，组织欢迎卡片、统计、快捷入口、订单、图片 |
| `AppSidebar.vue` | 左侧导航和分组 |
| `AppTopbar.vue` | 顶部账号、会员、在线状态 |
| `QuickEntryCard.vue` | 快捷入口卡片 |
| `RecentOrders.vue` | mock 订单表格 |
| `RecentGeneratedImages.vue` | mock 图片网格 |

## 路由建议

当前路由中 `/` 会重定向到 `/login`。首页改版后建议调整为：

```text
/          -> DashboardPage
/login     -> LoginPage
/ocr       -> OcrPage
/history   -> HistoryPage
```

注意：

- 不要加路由级强制登录拦截，除非任务明确要求。
- 首页可以显示 mock 用户信息。
- 已有页面内部的登录提示逻辑不要在本次 UI 改版中重构。

## Mock 数据建议

首页 mock 数据建议集中在 `DashboardPage.vue` 或独立文件。

如果独立文件，建议：

```text
desktop-app/src/pages/dashboardMock.ts
```

数据结构示例：

```ts
type DashboardStat = {
  label: string;
  value: string;
  helper: string;
  tone: "blue" | "green" | "orange" | "purple";
};

type QuickEntry = {
  title: string;
  description: string;
  icon: string;
  tone: "blue" | "orange" | "cyan" | "green" | "purple";
  route?: string;
  disabled?: boolean;
};

type RecentOrder = {
  orderNo: string;
  customerName: string;
  projectName: string;
  status: "已完成" | "进行中" | "待确认";
  updatedAt: string;
};
```

## 实施步骤

建议 CC 分阶段做，不要一次同时改功能和 UI。

### 第一步：新增 Dashboard 页面

目标：

- 新增 `DashboardPage.vue`。
- 让 `/` 指向 Dashboard。
- 首页能显示欢迎卡片、统计卡片、快捷入口、最近订单、最近生成图。

验收：

- `npm run build` 通过。
- 首页不依赖后端接口。
- OCR 页面仍可通过 `/ocr` 打开。

### 第二步：改造 App 外壳

目标：

- 把原来的顶部普通导航改成桌面工作台外壳。
- 左侧导航和顶部状态栏在首页及业务页面保持一致。
- `router-view` 放在内容区。

验收：

- 首页、OCR、历史记录页面都在同一外壳内显示。
- 当前路由菜单有高亮。
- 页面没有横向溢出。

### 第三步：补齐视觉细节

目标：

- 卡片边框、阴影、渐变、hover 状态完整。
- 表格、状态标签、图片网格对齐。
- 底部状态栏完整。

验收：

- 1280px 宽度下布局接近参考图。
- 1440px 到 1600px 宽度下不会显得过空或错位。
- 无明显字体过小、间距拥挤、颜色对比不足问题。

### 第四步：交互占位

目标：

- 快捷入口点击行为明确。
- 已有功能跳转已有页面。
- 未实现功能显示“即将开放”或 disabled 状态。

验收：

- 用户不会点了没反应。
- 未接后端的能力不会伪装成已经可用。

## 返工要求：根据用户截图 1 / 截图 2 修正

用户已提供当前实现截图，文件位于桌面 `UI` 文件夹：

- `C:\Users\123\Desktop\UI\1.png`：全屏效果。
- `C:\Users\123\Desktop\UI\2.png`：缩小窗口效果。

用户同时提供了新的标准参考图：

- `C:\Users\123\Desktop\123.jpg`：最终目标排版参考。

`123.jpg` 是版式标准，不只是大屏参考。小窗口时也必须保持和 `123.jpg` 一样的整体排版、区域比例和相对位置，只允许整体等比缩小，不允许重新排版成另一种布局。

当前实现不满足用户预期，必须按以下要求返工。

### 1. 全屏时主内容必须居中并合理铺开

截图 1 的问题：

- 主内容整体偏左。
- 右侧和底部留白过多。
- 页面像固定宽度内容贴在左边，而不是桌面工作台。
- 参考图的主工作区应在可用空间内居中，并有稳定的最大宽度。

修改要求：

- `app-main` 或 dashboard 根容器必须提供居中布局。
- dashboard 内容容器建议使用：

```css
.dashboard-page {
  width: min(100%, 1380px);
  margin: 0 auto;
  padding: 20px 24px 24px;
}
```

- 如果窗口宽度大于设计宽度，内容区居中，不要贴左。
- 如果窗口宽度在 `1280px` 到 `1600px`，内容应自然填满主要可视区域，不要出现大片空白。
- 大屏下订单区和生成图区应保持左右双栏，并按比例分配宽度。
- 不要把所有卡片写死为固定像素宽度后左对齐。

推荐主内容布局：

```css
.dashboard-grid {
  display: grid;
  gap: 16px;
}

.dashboard-top {
  display: grid;
  grid-template-columns: minmax(420px, 1.3fr) minmax(520px, 1fr);
  gap: 16px;
}

.dashboard-bottom {
  display: grid;
  grid-template-columns: minmax(520px, 1fr) minmax(520px, 1fr);
  gap: 16px;
}
```

### 2. 缩小窗口时整体缩小，不允许出现横向滑块

截图 2 的问题：

- 缩小窗口后页面没有整体适配。
- 出现明显滚动条/滑块，用户不能接受。
- 快捷入口和内容卡片像被裁切，而不是自适应。
- 用户明确要求：窗口缩小时应看到整个界面随窗口一起缩小，而不是出现滑动块让用户拖动查看。

修改要求：

- 不允许出现横向滚动条。
- 不允许主内容区和 sidebar 同时产生多个刺眼的内部滚动条。
- 缩小窗口时优先让整个工作台按比例缩小；其次才是少量响应式重排。
- 不要用固定总宽度撑破窗口。
- 不要只给外层加 `overflow: auto` 来掩盖布局问题。
- 不允许把小窗口适配做成“内容宽度不变 + 用户拖横向滚动条”。

核心策略：

- 以桌面工作台设计稿宽度作为基准，例如 `1366px` 或 `1440px`。
- 当可用宽度低于基准宽度时，计算缩放比例，让整个 dashboard canvas 缩小。
- 左侧导航、顶部栏、快捷入口、订单、图片区应作为一个整体缩放，而不是局部裁切。
- 缩放后仍要保持内容在窗口内完整可见。
- 小窗口版式必须和 `C:\Users\123\Desktop\123.jpg` 完全一致：欢迎区仍在左上，统计卡仍在右上，快捷入口仍为同一横向排列，最近订单仍在左下，最近生成图仍在右下。
- 不允许在小窗口下把订单区和生成图区改为上下排列。
- 不允许在小窗口下把快捷入口折成多行后破坏 `123.jpg` 的整体视觉比例。
- 不允许通过隐藏部分菜单、隐藏卡片、缩短为移动端布局来适配。

建议实现方式之一：

```css
.app-main {
  overflow: hidden;
}

.dashboard-scale-shell {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.dashboard-scale-canvas {
  width: 1366px;
  min-height: 760px;
  transform-origin: top left;
}
```

在 Vue 中根据容器宽度计算 scale：

```ts
const DESIGN_WIDTH = 1366;
const scale = Math.min(1, containerWidth / DESIGN_WIDTH);
```

应用到 canvas：

```vue
<div class="dashboard-scale-shell" ref="shellRef">
  <div
    class="dashboard-scale-canvas"
    :style="{ transform: `scale(${scale})`, width: `${DESIGN_WIDTH}px` }"
  >
    <!-- dashboard content -->
  </div>
</div>
```

注意：

- 使用 `transform: scale()` 后要同步处理容器高度，避免底部被裁切。
- 如果实现复杂，也可以使用 CSS `zoom`，但必须验证在 Tauri WebView 和浏览器预览中表现一致。
- 无论采用 `transform` 还是 `zoom`，验收标准都是：缩小窗口时没有横向滑块，用户能看到整体界面按比例缩小。
- 不要只依赖媒体查询把内容堆成长页面；用户要的是整体缩小，不是换成移动端长滚动页。
- 媒体查询只能用于细节微调，例如字号下限、滚动条隐藏、缩放容器高度修正，不能改变 `123.jpg` 的版式结构。

全局约束建议：

```css
html,
body,
#app {
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.app-right,
.app-main,
.dashboard-page {
  min-width: 0;
}
```

快捷入口建议：

```css
.quick-entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}
```

图片网格建议：

```css
.generated-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}
```

断点建议：

```css
@media (max-width: 1360px) {
  .dashboard-top,
  .dashboard-bottom {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1180px) {
  .app-sidebar {
    width: 208px;
  }

  .dashboard-page {
    padding: 16px;
  }
}
```

如果仍然出现横向滚动，必须定位是哪一个元素撑破宽度，并修正该元素的 `width`、`min-width`、`grid-template-columns`、缩放比例或 padding。不要接受“能滚动看到”作为合格结果。

### 3. 降低高饱和高亮，避免 HDR 式刺眼观感

截图 1 和截图 2 的问题：

- 欢迎卡片和菜单高亮蓝色过亮。
- 纯色图片占位块饱和度过高。
- 多处图标背景和标签同时发亮，视觉焦点混乱。
- 整体有类似 HDR 过曝的观感。

修改要求：

- 降低蓝色主高亮的亮度和饱和度。
- 欢迎卡片不要使用大面积高亮纯蓝，应改为更暗的深蓝渐变。
- 图片占位块不要使用纯色大色块，应改为暗色渐变、低透明度纹理或真实图片缩略图。
- disabled / coming soon 标签必须低对比，不要抢视觉。
- 当前菜单高亮只保留一个强焦点，不要让所有功能卡片都像主按钮。

建议替换色值：

```css
:root {
  --blue: #2f6fed;
  --blue-strong: #1f4fbf;
  --blue-soft: rgba(47, 111, 237, 0.16);
  --panel-highlight: linear-gradient(135deg, #132b4d 0%, #183b73 52%, #1d4f9a 100%);
}
```

欢迎卡片建议：

```css
.welcome-card {
  background:
    radial-gradient(circle at 18% 28%, rgba(47, 111, 237, 0.22), transparent 34%),
    linear-gradient(135deg, #10213b 0%, #142b4e 48%, #163f7c 100%);
}
```

图片占位卡片建议：

```css
.generated-thumb {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.08), transparent),
    linear-gradient(135deg, rgba(47, 111, 237, 0.38), rgba(15, 23, 42, 0.92));
  filter: saturate(0.82);
}
```

不要使用下面这种效果：

- 大面积 `#2458ff`、`#2563eb` 纯色填充。
- 多个高亮卡片同时使用强 box-shadow。
- 纯红、纯绿、纯紫大块背景。
- 文本、图标、边框、背景全部同时高亮。

### 4. 顶部白色窗口栏必须处理为和整体色调一致

截图中最上方白色栏会破坏整体观感。

必须先区分来源：

- 如果是在浏览器/Vite preview 中看到的白色顶部栏，那是浏览器或系统窗口 chrome，Vue 页面 CSS 无法改变。
- 如果是在 Tauri 桌面窗口中看到的白色顶部栏，则需要通过 Tauri 窗口配置或自定义标题栏处理。

当前任务默认禁止修改 Tauri 配置；如果 CC 需要改 `desktop-app/src-tauri/**` 或 `tauri.conf.json` 才能处理顶部窗口栏，必须先停下来说明方案并等待用户确认。

可接受方案：

- 方案 A：本轮只修 Vue 页面，明确说明白色顶部栏来自预览窗口/系统 chrome，打包桌面壳需另开 Tauri 标题栏任务。
- 方案 B：经用户确认后，使用 Tauri 深色窗口主题或自定义标题栏，让顶部栏背景与 `--bg-sidebar` / `--bg-app` 一致。

不可接受方案：

- 在页面内部加一条深色假标题栏，但原生白色栏仍然存在。
- 忽略白色顶部栏，声称已经完成视觉统一。
- 未经确认直接修改 Tauri 权限、窗口配置或打包配置。

### 5. 只保留必要滚动，避免双滚动条

桌面工作台应尽量保持单一滚动策略。

要求：

- 页面主区域可以纵向滚动。
- 左侧导航如果内容超出，可以有内部滚动，但滚动条必须弱化，不要出现亮灰色粗滑块。
- 不允许主窗口横向滚动。
- 不允许内容卡片内部出现不必要滚动条。
- 缩小窗口时优先整体缩放，其次才是重排和压缩，不允许用横向滚动解决。

滚动条弱化建议：

```css
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(100, 116, 139, 0.45) transparent;
}

*::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.42);
  border-radius: 999px;
}
```

### 6. 返工验收截图要求

CC 返工后必须提供至少两张截图：

- 全屏截图：接近 `C:\Users\123\Desktop\UI\1.png` 的窗口尺寸。
- 缩小窗口截图：接近 `C:\Users\123\Desktop\UI\2.png` 的窗口尺寸。

验收重点：

- 全屏和缩小窗口都必须保持 `C:\Users\123\Desktop\123.jpg` 的同一排版结构。
- 全屏主内容居中，不贴左。
- 大屏没有大片无意义空白。
- 缩小窗口时整个界面整体缩小，没有横向滑块。
- 快捷入口、订单、生成图区域没有被硬裁切。
- 高亮颜色不刺眼。
- 顶部白色窗口栏的来源和处理方案已说明；如果已经获得 Tauri 修改确认，则必须实际统一为深色。

## 禁止范围

本任务只做桌面前端 UI。

禁止：

- 修改云端后端。
- 修改数据库 schema 或迁移。
- 接入真实 AI provider。
- 新增真实扣费逻辑。
- 引入 Docker。
- 为首页 mock 数据启动本地数据库、缓存或服务。
- 大规模重构登录、OCR、历史记录业务逻辑。
- 把 UI 改版和 Tauri 打包问题混在同一个提交里。

如发现当前仓库有与本任务无关的未提交变更，CC 应先停止并向用户说明，不要顺手整理。

## 验收标准

完成后应满足：

- 首页整体视觉接近参考图的深色桌面工作台。
- 左侧导航、顶部状态栏、欢迎卡片、统计卡片、快捷入口、最近订单、最近生成图、底部状态栏全部可见。
- 全屏时主内容在可用区域内居中，不能贴左，不能右侧大面积空白。
- 缩小窗口时界面整体缩小，并保持和 `C:\Users\123\Desktop\123.jpg` 一样的排版；不能出现横向滑块，不能靠拖动滑块查看被裁切内容，不能改成另一套小屏布局。
- 高亮颜色降低饱和度，不能出现 HDR 式刺眼观感。
- 顶部白色窗口栏必须说明来源；如需 Tauri 配置改动，必须先获得用户确认。
- 滚动策略清晰，不允许多个明显内部滚动条破坏桌面观感。
- 首页使用 mock 数据，不依赖后端和本地服务。
- OCR 页面、登录页面、历史记录页面仍能访问。
- `desktop-app` 下执行 `npm run build` 通过。
- `git diff --check` 通过。
- 改动范围主要集中在 `desktop-app/src` 和本说明文档。

## 给 CC 的执行指令

可以直接把下面内容交给 CC：

```text
请按 docs/26-desktop-dashboard-ui-redesign.md 实现桌面端首页 UI 改版。

注意：用户已反馈当前实现不合格，必须优先处理文档中的“返工要求：根据用户截图 1 / 截图 2 修正”。

本任务只做前端 UI 壳，不接后端、不改数据库、不用 Docker、不实现真实 AI 调用。

优先实现：
1. 新增 DashboardPage，把 `/` 改为首页。
2. 改造桌面端 App 外壳为左侧导航 + 顶部状态栏 + 内容区 + 底部状态栏。
3. 用 mock 数据实现欢迎卡片、统计卡片、快捷入口、最近订单、最近生成效果图。
4. OCR 快捷入口跳转现有 `/ocr`，历史或订单入口可暂时跳 `/history` 或显示占位。
5. 未实现功能必须明确标注“即将开放”或 disabled，不要伪装成可用。
6. 全屏和缩小窗口都必须保持 `C:\Users\123\Desktop\123.jpg` 的同一排版；缩小窗口时整个界面要整体缩小，不能出现横向滑块。
7. 降低蓝色和图片占位块饱和度，避免 HDR 式刺眼效果。
8. 顶部白色窗口栏要说明来源；如需改 Tauri 配置，先停下来等用户确认。

验收前必须运行：
1. cd desktop-app
2. npm run build
3. git diff --check

不要修改后端、数据库、provider、计费、真实鉴权逻辑。
```
