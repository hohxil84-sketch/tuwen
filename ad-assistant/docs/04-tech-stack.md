# 04 技术栈

## 桌面端

固定方向：
- Tauri 2
- Vue 3
- TypeScript
- Pinia
- SQLite
- Python FastAPI 本地服务
- 本地 sidecar 或 CLI 调用

MVP 不允许未经确认替换桌面技术栈。

## 云端后台

固定方向：
- Python FastAPI
- PostgreSQL 或 MySQL
- Redis
- Celery 或 RQ
- 后台管理系统

数据库选型在真正建表前必须确认。

## 官网

固定方向：
- Next.js
- Tailwind CSS

官网 MVP 页面：
- 下载页
- 价格页
- 教程页
- 注册入口
- SEO 基础配置

## 本地工具优先级

MVP 优先：
- PaddleOCR
- vtracer
- ImageMagick

BACKLOG：
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

## 依赖规则

新增第三方 SDK 属于重大变更，必须先确认。

升级核心依赖属于重大变更，必须先确认。

核心依赖包括：
- Tauri
- Vue
- TypeScript
- Pinia
- FastAPI
- SQLAlchemy 或 ORM
- 数据库驱动
- Redis 客户端
- Celery/RQ
- Next.js
- Tailwind CSS
- AI Provider SDK
- OCR、图像处理、矢量化核心工具

