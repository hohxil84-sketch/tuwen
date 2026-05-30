# 13 模块路线图

## 状态定义

`MVP_REQUIRED`：当前必须开发。

`MVP_OPTIONAL`：MVP 可选，必须用户确认。

`BACKLOG`：后期待开发，当前禁止。

`FUTURE`：长期设想，当前禁止。

`BLOCKED`：依赖未完成，当前禁止。

## P0 MVP_REQUIRED

- 登录/授权
- OCR
- 图片上传
- OCR 结果展示
- 本地历史记录
- 使用统计
- AI 算力记录
- 基础后台

## P1 MVP_OPTIONAL

以下功能必须用户确认后才能开发：
- 转矢量
- 基础修图
- 高级 AI 修图
- AI 门头效果图

## BACKLOG

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
- rembg
- Real-ESRGAN
- Ghostscript
- Poppler
- Inkscape CLI
- LibreOffice Headless
- python-pptx
- ComfyUI
- Stable Diffusion
- Flux

## Sprint-01

Sprint-01 只允许包含：
- 项目基础结构
- 登录授权最小闭环
- OCR 最小闭环
- OCR 历史记录
- 使用统计基础表
- provider_call_log 表

