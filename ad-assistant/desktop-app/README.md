# Desktop App — AI 图文广告助手桌面客户端

## 职责

- 用户界面（登录页、工作台、OCR 结果展示、历史记录）
- 图片选择和预览
- 调用本地 FastAPI 服务（OCR）
- 调用云端业务 API（Auth、OCR、Usage、Credit）
- 展示云端返回的权限、套餐、额度状态
- 本地 SQLite 历史记录和任务状态
- 系统安全存储 Token（不存明文）

## 技术栈

- **框架**: Tauri 2
- **前端**: Vue 3 + TypeScript（严格模式）
- **状态管理**: Pinia
- **本地数据库**: SQLite
- **本地服务**: Python FastAPI（sidecar 方式）

## 目录结构

```
desktop-app/
  src/             # Vue 3 前端源码
  src-tauri/       # Tauri 2 配置和 Rust 代码
  local-service/   # Python FastAPI 本地服务
  local-tools/     # 本地 CLI 工具封装
  migrations/      # 本地 SQLite 迁移
  tests/           # 前端和本地服务测试
```

## Sprint-01 状态

当前为最小工程骨架。所有模块目录已预留，**尚未实现业务逻辑**。

## 安全红线

- 不持有第三方 AI API Key
- 不直接调用 OpenAI / DeepSeek / Claude / ComfyUI 等第三方 API
- 不进行真实扣点计算和扣除
- 不进行套餐最终判断和权限判定
- 不进行 Provider 路由决策
- 不存储明文 Token
