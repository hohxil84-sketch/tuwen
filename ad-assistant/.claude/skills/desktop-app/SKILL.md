---
name: desktop-app
description: 前端桌面端实现 Skill — Tauri 2 + Vue3 + Pinia + SQLite，重点是工作台 UI、本地历史、调用本地服务和云端 API。触发时机：开发桌面端功能、UI 页面、本地存储、调用本地服务或云端 API 时。
---

# 前端桌面端实现 Skill

## 技术栈（固定，不可随意替换）

- **框架**: Tauri 2
- **前端**: Vue 3 + TypeScript（严格模式，禁止 `any` 绕过类型）
- **状态管理**: Pinia
- **本地数据库**: SQLite
- **本地服务**: Python FastAPI（sidecar 方式）
- **UI 风格**: 参考 `docs/18-ui-style-guide.md`

## 桌面端职责边界

### ✅ 桌面端负责

- 用户界面（登录页、工作台、OCR 结果展示、历史记录）
- 图片选择和预览
- 调用本地 FastAPI 服务（OCR）
- 调用云端业务 API（Auth、OCR、Usage、Credit）
- 展示云端返回的权限、套餐、额度状态
- 本地 SQLite 历史记录和任务状态
- 系统安全存储 Token（不存明文）

### ❌ 桌面端绝不负责

- 持有第三方 AI API Key
- 直接调用 OpenAI / DeepSeek / Claude / ComfyUI 等第三方 API
- 真实扣点计算和扣除
- 套餐最终判断和权限判定
- Provider 路由决策
- 通用远程命令执行

## 目录结构

```text
desktop-app/
  README.md
  src/                  # Vue 3 前端源码
  src-tauri/            # Tauri 2 配置和 Rust 代码
  local-service/        # Python FastAPI 本地服务
  local-tools/          # 本地 CLI 工具封装
  migrations/           # 本地 SQLite 迁移
  tests/                # 前端和本地服务测试
```

## 本地数据库规范

SQLite 可存储：
- `ocr_history` — OCR 历史记录
- `local_task_state` — 本地任务状态
- `app_settings` — 非敏感应用设置
- `offline_license_cache` — 离线授权缓存签名包

SQLite 绝不存储：
- 明文 access token / refresh token
- Provider API Key
- 用户密码

## 本地服务规范

本地 FastAPI 服务只做受控封装：

- PaddleOCR — OCR 识别

每个工具必须：
- 参数白名单校验
- 文件类型校验
- 文件大小限制
- 超时控制
- 错误码统一映射
- 日志脱敏

## UI 开发规范

- API 类型来自 `shared/typescript`
- 组件不得包含 Provider Key、扣费逻辑、套餐判断
- 状态管理集中在 Pinia Store
- 本地存储通过 Tauri SQLite Plugin

## MVP Sprint-01 页面

只允许开发：
- 登录页
- 授权状态区域
- 图片上传区域
- OCR 结果展示区域
- OCR 历史列表
- 使用统计基础区域

禁止开发未来功能页面（PPT、Skill 市场、插件系统、AI 工作流、自动报价、PS/CDR 控制）。

## Tauri 权限

修改 `src-tauri` 权限配置属于重大变更，必须先确认。
