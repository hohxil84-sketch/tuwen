# 09 桌面端指南

## 职责

桌面端负责：
- 用户界面
- 图片选择和预览
- OCR 结果展示
- 本地历史记录
- 调用本地 FastAPI 服务
- 调用云端业务 API
- 展示云端授权、套餐、额度状态

桌面端不负责：
- 第三方 AI API Key
- 真实扣点
- 套餐最终判断
- 高级 AI 权限最终判断
- Provider 路由最终判断

## 本地数据库

桌面端 SQLite 可存储：
- OCR 历史记录
- 本地任务状态
- 最近打开文件记录
- 非敏感设置
- 离线授权缓存签名包

不得明文存储：
- access token
- refresh token
- Provider API Key
- 用户密码

## 本地服务

本地 FastAPI 服务用于封装：
- PaddleOCR

禁止本地服务提供通用远程命令执行接口。

修改本地 Python 服务启动方式属于重大变更，必须先确认。

## 云端 API 客户端

Sprint-02 Task-05 新增：

- `desktop-app/src/services/cloudApi.ts` — 云端 API HTTP 客户端
  - `POST /api/v1/auth/login` — 登录
  - `POST /api/v1/auth/logout` — 登出（best-effort）
  - `POST /api/v1/mock-ai/ad-copy` — Mock AI 广告文案生成
  - 默认 base URL: `http://127.0.0.1:8000`，可通过 `VITE_CLOUD_API_BASE_URL` 覆盖
  - 登录后自动附加 `Authorization: Bearer <access_token>`
  - 绝不调用第三方 AI API
  - 绝不记录 token、密码、设备指纹或用户文本

- `desktop-app/src/stores/authStore.ts` — Pinia 内存态 Auth Store
  - Token 仅存 JavaScript 内存，不落盘
  - 提供 login/logout/callMockAdCopy 方法
  - 错误消息自动脱敏为中文用户友好提示

## UI MVP 页面

当前允许包含：
- 登录页（含云端登录表单）
- 授权状态区域
- 图片上传区域
- OCR 结果区域
- OCR 历史列表
- 使用统计基础区域
- Mock AI 广告文案面板（仅 Mock，标注清晰）

不得开发：
- PPT
- Skill 市场
- 插件系统
- AI 工作流
- 自动报价
- PS/CDR 自动控制
- 通用 Prompt 执行 UI
- Provider/Model 选择器

