# AI 图文广告助手

面向图文店、广告店、快印店、喷绘写真店、门头广告店、CDR/PS 从业者的按钮化 AI 工作台。

本项目不是通用聊天 AI，而是围绕图文广告行业高频任务提供桌面端、云端授权、AI Provider、算力计费、历史记录和后台管理能力。

## 产品边界

当前只允许开发 `tasks/current-task.md` 明确列出的功能。

MVP P0：
- 登录/授权
- OCR
- 图片上传
- OCR 结果展示
- 本地历史记录
- 使用统计
- AI 算力记录
- 基础后台

MVP P1：
- 转矢量
- 基础修图
- 高级 AI 修图
- AI 门头效果图

当前禁止开发：
- PPT
- Skill 市场
- 插件系统
- AI 工作流
- 自动报价
- 微信机器人
- 云同步
- PS 自动控制
- CDR 自动控制
- 企业私有部署

## Monorepo 结构

```text
ad-assistant/
  docs/
  desktop-app/
  cloud-backend/
  official-website/
  shared/
  tasks/
  CODEX.md
  CLAUDE.md
  README.md
```

## 技术组成

桌面端：
- Tauri 2
- Vue 3
- TypeScript
- Pinia
- SQLite
- Python FastAPI 本地服务
- 本地工具、sidecar、CLI 调用

云端后台：
- Python FastAPI
- PostgreSQL 或 MySQL
- Redis
- Celery 或 RQ
- 后台管理系统

官网：
- Next.js
- Tailwind CSS
- 下载页、价格页、教程页、注册入口、SEO

共享层：
- OpenAPI
- DTO
- TypeScript 类型
- 错误码
- 常量
- SDK

## 安全原则

优先级固定为：

安全 > 稳定 > 可维护 > 可扩展 > 功能数量 > 开发速度

禁止：
- API Key 放客户端
- 客户端直接调用第三方 AI API
- 客户端直接扣点
- 客户端决定套餐和权限
- 本地保存明文 Token
- 绕过云端授权
- 未授权调用高级 AI
- 自动升级核心依赖
- 自动大规模重构
- 未确认修改数据库结构、API 契约、Provider 接口、授权、支付、Token、Tauri 权限

必须：
- 云端授权校验
- 设备绑定
- Token 刷新机制
- 离线授权缓存
- 请求限流
- 风控日志
- 异常设备封禁
- 点数云端扣除
- Provider 调用日志
- 成本统计

## AI 算力商业模式

采用月费/年费 + AI 算力额度 + 超额算力购买。

初始定价方向：
- 标准版：359 元/月
- 专家版：559 元/月
- 企业版：999 元/月

不允许买断制。
不允许无限 AI 会员。
不允许固定写死所有功能点数。

AI 扣费链路：
1. Provider 返回 token、图片成本、GPU 时间或 provider 成本。
2. 后台计算 `estimated_cost`。
3. `estimated_cost` 换算为 AI 算力。
4. 云端从用户额度扣除。
5. 所有调用写入 `provider_call_log`。

## 开发流程

1. 先写任务单。
2. 用户确认任务单。
3. 一个模块一个 Git 分支。
4. Claude Code + DeepSeek 执行任务单。
5. Codex Review 做架构、安全、API、数据库、Provider、成本审查。
6. Codex Review 通过后才允许提交。
7. 通过验收后再进入下一个任务。

没有任务单，不允许写代码。
没有用户确认，不允许开发未来功能。
没有 Codex Review 通过结论，不允许提交。

Git 详细规则见 `docs/20-agent-git-guardrails.md`。
