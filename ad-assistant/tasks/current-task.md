# 当前任务：Sprint-01 Task-04 OCR 最小闭环

## 状态

`MVP_REQUIRED` — 等待 Codex Review 任务单（第 4 轮，修复阻断问题）

## 分支

`feature/sprint-01-ocr-minimal`（基于 `main`，commit 56aadb2）

## 前置任务

- Task-01 项目骨架搭建 ✅ 已完成
- Task-02 Auth/Device 方案设计 ✅ 已完成
- Task-03 Auth/Device 实现 ✅ 已完成（已合并到 main）

## 背景

OCR 是 MVP P0 核心功能。图文广告行业高频需求：从名片、传单、喷绘稿、门头照片中提取文字，用于改字、排版、报价。

Sprint-01 只做 **OCR 最小闭环（纯本地）**：用户在桌面端选图 → 本地 PaddleOCR 引擎识别 → 结果显示在 UI → 存入本地 SQLite 历史。

本地 OCR 引擎使用 PaddleOCR。OCR 推理过程不调用云端 AI Provider、不扣算力、不上传图片或识别内容。后续 Task 再扩展云端 OCR Provider、使用统计上报和高级识别能力。

### PaddleOCR 模型缓存策略

PaddleOCR 首次运行需要下载模型文件（约 50-100MB），Task-04 采用以下策略：

**开发环境初始化（首次安装，需要联网）：**
- 首次安装依赖后，在开发/测试环境中运行一次初始化脚本，预下载模型到本地缓存目录
- 默认模型缓存目录：`~/.paddleocr/`（PaddleOCR 默认路径，可通过环境变量 `PADDLEOCR_HOME` 覆盖）
- 初始化脚本明确提示用户"正在下载 OCR 模型文件，仅需一次"，显示下载进度

**运行时行为（支持离线）：**
- 运行时优先使用已缓存的模型文件，不主动联网
- 如模型缓存已存在，OCR 引擎直接加载，无需网络
- 如模型缓存不存在（首次运行且未初始化），返回明确错误 `OCR_MODEL_NOT_FOUND`，附带操作指引（"请先运行初始化脚本下载模型，或手动下载模型文件到 ~/.paddleocr/"）

**下载失败处理：**
- 初始化脚本下载失败时，返回明确错误码和重试建议
- 不静默失败、不无限重试
- 错误信息中标注当前网络状态检查提示

**离线环境部署：**
- 支持将模型文件预置到安装包中，或通过离线包手动复制到缓存目录
- 离线环境检测到模型缓存目录已就绪时，不尝试联网

> 总结：Task-04 **允许开发环境联网下载模型**，运行时 **必须支持已缓存模型的离线使用**。不要求"绝不联网"，但 OCR 推理过程和用户使用阶段不依赖网络。

## 本次只开发什么

### 1. PaddleOCR Wrapper 完整实现

文件：`desktop-app/local-service/wrappers/paddleocr.py`

- 封装 PaddleOCR 调用，禁止任意参数透传
- 参数白名单：`lang`（默认 `ch`）、`use_angle_cls`（默认 `true`）、`det_db_thresh`、`rec_batch_num`
- 文件类型校验：扩展名白名单（png / jpg / jpeg / bmp / tiff / webp）+ MIME 类型校验
- 文件大小限制：默认 50MB（可配置）
- 路径限制：只允许处理指定目录内的文件（禁止绝对路径穿越）
- 超时控制：默认 60s（可配置）
- 错误码映射：PaddleOCR 内部异常映射为统一错误码，不泄露内部堆栈
- 日志脱敏：不记录文件内容、用户路径中的用户名
- 返回结构遵循 `docs/10-local-ai-tools-guide.md` 规范：

```json
{
  "text": "识别出的全文",
  "blocks": [
    {
      "text": "单块文本",
      "confidence": 0.98,
      "bbox": [0, 0, 100, 40]
    }
  ],
  "engine": "paddleocr",
  "duration_ms": 1200
}
```

### 2. 本地 OCR API 端点

文件：`desktop-app/local-service/routes/ocr.py`

- `POST /local/ocr`
  - 接受 multipart/form-data（image 文件字段）
  - 校验文件类型（扩展名 + MIME）
  - 校验文件大小
  - 调用 PaddleOCR wrapper
  - 返回统一结构 `{success, data, error, request_id}`
- `GET /local/ocr/health` — OCR 引擎健康检查（PaddleOCR 是否就绪）
- 参数校验错误返回 422
- 不在本地服务保存明文 Token / API Key

### 3. 本地服务入口更新

文件：`desktop-app/local-service/main.py`

- 注册 OCR 路由
- 启动时预加载 PaddleOCR 模型（或首次调用时懒加载）
  - **关键约束：运行时初始化 PaddleOCR 必须禁用自动下载。** 缓存就绪则加载；缓存缺失只能返回 `OCR_MODEL_NOT_FOUND`，不得触发联网下载
  - 模型下载只允许在初始化脚本（`scripts/init_paddleocr_models.py`）中执行，禁止在服务入口或路由中自动下载
- 添加 CORS 中间件（仅允许 localhost 来源）

### 4. 本地 SQLite OCR 历史

文件：`desktop-app/local-service/history.py`（新文件）

- `ocr_history` 表 DDL：
  - `id` TEXT PRIMARY KEY (UUID v4)
  - `image_filename` TEXT NOT NULL（原始文件名，用于 UI 展示，不含路径）
  - `image_hash` TEXT NOT NULL（图片文件 SHA-256 前 16 位 hex，用于去重校验）
  - `local_copy_path` TEXT（应用沙箱内相对路径，如 `ocr_images/20250530_abc123.png`；可选，仅当本地服务将图片副本保存到沙箱目录时填写）
  - `text` TEXT（识别全文）
  - `blocks_json` TEXT（文本块 JSON，SQLite 不支持原生 JSON 类型）
  - `engine` TEXT（`paddleocr`）
  - `duration_ms` INTEGER
  - `created_at` TEXT（ISO 8601 UTC）
- API：
  - `GET /local/ocr/history?limit=50&offset=0` — 返回历史列表（按时间倒序）
  - `GET /local/ocr/history/{id}` — 返回单条 OCR 结果详情
- 安全要求：
  - ❌ **禁止保存用户原始绝对路径**（如 `C:\Users\张三\Desktop\报价单.png` 或 `/home/zhangsan/报价单.png`）
  - ❌ **禁止保存包含用户名、客户名或其他 PII 的目录路径**
  - ✅ `image_filename` 只存文件名，不存路径
  - ✅ `local_copy_path` 只允许应用沙箱内相对路径（如 `ocr_images/<uuid>.png`）
  - ✅ 如需在历史页预览原图，使用 `local_copy_path` 引用沙箱内副本
  - ✅ OCR 完成后，本地服务将图片副本存入沙箱目录，记录 `local_copy_path`
  - ❌ 不存储：明文 Token、密码、Provider Key、原始图片二进制

### 5. 桌面端 OCR 工作台页面

文件：`desktop-app/src/pages/OcrPage.vue`

- 图片选择区域：
  - 点击上传按钮（文件选择器）
  - 拖拽上传区域（drag & drop）
  - 图片预览（缩略图或原图预览）
  - 支持格式：png / jpg / jpeg / bmp / tiff / webp
- OCR 触发按钮
- 识别状态指示（loading / 进度）
- 识别结果展示：
  - 全文显示区域（可选中复制）
  - 文本块列表（按置信度排序，显示 bbox 坐标）
  - 引擎名称和耗时
- 错误状态展示（统一错误提示，不暴露内部错误详情）

### 6. 桌面端 OCR 历史列表页面

文件：`desktop-app/src/pages/HistoryPage.vue`

- 历史记录列表（通过本地服务 API 查询 SQLite）
- 每条显示：文件名、识别时间、文本前 100 字符预览
- 点击查看完整 OCR 结果
- 分页加载（每页 50 条）

### 7. 前端 API 调用层

新文件（如需要）：`desktop-app/src/services/ocrService.ts`

- 封装对 `http://127.0.0.1:9100/local/ocr` 的调用
- 图片文件上传（FormData）
- 错误处理（超时、网络错误、服务不可用）
- 统一响应解析

### 8. 自动化测试

- 本地 PaddleOCR wrapper 单元测试（mock PaddleOCR，测试参数校验、文件校验、错误码映射）
- 本地 OCR API 端点测试（测试文件上传、参数校验、响应格式）
- 本地 OCR 历史 API 测试（保存、查询、分页）
- 目标：≥ 12 个测试用例，全部在本地运行（不依赖云端服务）

## 本次不开发什么

- ❌ 云端 OCR task 记录 API（`POST/GET /api/v1/ocr/tasks`）— 后续 Task
- ❌ 云端使用统计上报（`POST /api/v1/usage/events`）— 后续 Task
- ❌ 云端 OCR 数据库模型（`ocr_tasks` 表）— 后续 Task
- ❌ 云端 DDL 草案（`005_ocr_tasks.sql`）— 后续 Task
- ❌ usage_events 表写入 — 后续 Task
- ❌ provider_call_log 写入 — 后续 Task
- ❌ 云端 AI Provider OCR（调用云端大模型做 OCR）— 后续 Task
- ❌ OCR 扣费 / 算力扣除（本地 OCR 为免费功能，不涉及扣费）— 后续 Task
- ❌ OCR 结果编辑（修改识别文本、合并/拆分文本块）
- ❌ 批量 OCR（一次选多张图）
- ❌ OCR 结果导出（复制到剪贴板除外）
- ❌ 高级 OCR 能力：表格识别、手写体识别、印章识别、二维码/条形码
- ❌ 图片预处理增强（去噪、纠偏、超分辨率）
- ❌ 自定义 OCR 区域选择（ROI 框选）
- ❌ 转矢量（P1）
- ❌ 基础修图 / 高级 AI 修图 / AI 门头效果图（P1）
- ❌ PPT / Skill 市场 / 插件系统 / AI 工作流 / 自动报价 / 微信机器人 / 云同步
- ❌ PS 自动控制 / CDR 自动控制 / 企业私有部署
- ❌ 桌面端打包 / 分发 / 自动更新
- ❌ 本地服务进程管理（Tauri sidecar 配置）— 后续 Task
- ❌ 额度系统（credit_accounts / credit_ledger）— 后续 Task
- ❌ 账号锁定实现（仍按 Task-03 约定推迟）
- ❌ 执行真实数据库迁移
- ❌ 修改已有云端代码或数据库模型

## 允许修改哪些文件

允许在确认后修改：

本地服务：
- `desktop-app/local-service/main.py`
- `desktop-app/local-service/routes/ocr.py`
- `desktop-app/local-service/routes/__init__.py`
- `desktop-app/local-service/wrappers/paddleocr.py`
- `desktop-app/local-service/wrappers/__init__.py`
- `desktop-app/local-service/history.py`（新文件）
- `desktop-app/local-service/requirements.txt`（新文件，本地服务依赖声明）
- `desktop-app/local-service/scripts/init_paddleocr_models.py`（新文件，模型初始化脚本，仅开发/测试环境使用）

桌面端 UI：
- `desktop-app/src/pages/OcrPage.vue`
- `desktop-app/src/pages/HistoryPage.vue`
- `desktop-app/src/services/ocrService.ts`（新文件）
- `desktop-app/src/router.ts`
- `desktop-app/src/main.ts`
- `desktop-app/src/components/`（新组件，如有需要）
- `desktop-app/package.json`（允许调整构建配置，但不新增 npm 依赖）

测试：
- `desktop-app/local-service/tests/`（新目录，本地服务测试）
- `desktop-app/tests/`（桌面端基础测试，如有需要）

构建与运行产物忽略：
- `.gitignore`（仓库根目录，排除 OCR runtime artifacts 和 review artifacts）
- `desktop-app/tsconfig.node.json`（修复 vue-tsc TypeScript 项目引用构建）
- `desktop-app/vite.config.ts`（修复 Vite @ 路径别名构建）
- `desktop-app/package-lock.json`（npm install 生成，锁定前端依赖版本）

任务管理：
- `tasks/current-task.md`

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `cloud-backend/` 下所有文件（包括 `app/api/ocr.py`、`app/api/usage.py`、`app/models/`、`app/schemas/`、`migrations/` 等）— Task-04 不涉及云端
- API 契约正式文件（`docs/05-api-contract.md`）
- shared DTO 正式文件
- Tauri 权限配置
- 自动更新配置
- Provider 接口定义（`cloud-backend/app/providers/`）
- 支付逻辑
- Auth/Device 已实现的代码（`auth.py`, `device.py`, `deps.py`, `auth_service.py`, `device_service.py`, `security.py`）
- 已完成的数据库模型（`user.py`, `device.py`, `auth_session.py`, `risk_log.py`）
- 已完成的 DDL 文件（`001_users.sql`, `002_devices.sql`, `003_auth_sessions.sql`, `004_risk_logs.sql`）
- 本地 Python 服务启动方式（不能改为其他端口或启动方式）
- 配置文件 `cloud-backend/app/core/config.py`

## 新增依赖申请

Task-04 需要在本地服务引入 PaddleOCR 引擎，以下 4 个依赖需 Codex Review 批准：

### 申请 7：paddlepaddle（CPU 版）

| 项目 | 说明 |
|------|------|
| **包名** | `paddlepaddle` |
| **版本** | `>=3.0.0`（CPU 版本，`paddlepaddle` 不含 `-gpu` 后缀） |
| **用途** | PaddleOCR 底层深度学习推理框架 |
| **许可证** | Apache 2.0 |
| **体积** | 约 300-400MB（含预编译算子 wheel） |
| **依赖链** | `numpy`, `protobuf`, `Pillow` 等（Paddle 核心依赖） |
| **安全风险** | 低。百度开源，Apache 2.0 许可证，有活跃社区维护 |
| **替代方案** | 1. 云端 OCR API（需网络、有延迟、有成本）2. Tesseract OCR（中文识别准确率显著低于 PaddleOCR）3. EasyOCR（PyTorch 依赖，体积更大） |
| **推荐理由** | PaddleOCR 是当前中文 OCR 准确率最高的开源方案，CPU 推理可用，离线运行无网络依赖，Apache 2.0 许可证无合规风险 |

### 申请 8：paddleocr

| 项目 | 说明 |
|------|------|
| **包名** | `paddleocr` |
| **版本** | `>=3.0.0` |
| **用途** | OCR 模型加载、文本检测、文字识别 Pipeline |
| **许可证** | Apache 2.0 |
| **体积** | 约 5-10MB（Python 代码 + 配置文件），首次运行自动下载模型文件（约 50-100MB） |
| **依赖链** | `paddlepaddle`, `numpy`, `opencv-python-headless`, `Pillow`, `pyclipper`, `shapely`, `lanms-neo` |
| **安全风险** | 低。百度开源，模型文件为 Paddle 格式，仅本地推理，不上传数据 |
| **替代方案** | 1. 手写 Paddle 推理代码（重复造轮子）2. Surya OCR（英文为主，中文不如 PaddleOCR）3. Tesseract（中文准确率低） |
| **推荐理由** | PaddleOCR 中文识别 SOTA、API 简洁、支持 80+ 语言、社区活跃、离线运行、首次自动下载模型 |

### 申请 9：opencv-python-headless

| 项目 | 说明 |
|------|------|
| **包名** | `opencv-python-headless` |
| **版本** | `>=4.10.0` |
| **用途** | 图像预处理（读文件、尺寸调整、格式转换），PaddleOCR 输入预处理依赖 |
| **许可证** | Apache 2.0 |
| **体积** | 约 30-50MB（预编译 wheel，headless 版不含 GUI 模块） |
| **依赖链** | `numpy`（共享依赖） |
| **安全风险** | 低。使用 headless 版本（无 GUI 功能），减少不必要的依赖面。OpenCV 是计算机视觉领域最广泛使用的库 |
| **替代方案** | 1. `Pillow`（纯图像读写，但 PaddleOCR 内部部分预处理依赖 OpenCV）2. `opencv-python`（含 GUI 模块，体积更大，headless 更合适） |
| **推荐理由** | PaddleOCR 官方依赖链要求 OpenCV，headless 版本减少不必要的 GUI 依赖，最广泛的图像处理库 |

### 申请 10：python-multipart

| 项目 | 说明 |
|------|------|
| **包名** | `python-multipart` |
| **版本** | `>=0.0.12` |
| **用途** | FastAPI 文件上传解析（multipart/form-data） |
| **许可证** | Apache 2.0 |
| **体积** | 约 0.1MB（纯 Python） |
| **依赖链** | 无强制依赖 |
| **安全风险** | 低。FastAPI 官方推荐的文件上传依赖 |
| **替代方案** | 1. `aiofiles`（异步文件写入，但不负责解析 multipart）2. 手写 multipart 解析（不安全） |
| **推荐理由** | FastAPI 官方推荐，广泛使用，体积小 |

### 桌面端依赖（Node.js）

| 依赖 | 版本 | 用途 | 许可证 | 风险 |
|------|------|------|--------|------|
| 无新依赖 | — | 使用已有 Vue 3 + TypeScript 栈，前端文件上传为浏览器原生 API | — | 无 |

### 云端后台依赖（Python）

| 依赖 | 版本 | 用途 | 许可证 | 风险 |
|------|------|------|--------|------|
| 无新依赖 | — | Task-04 不涉及云端后台 | — | 无 |

### 依赖汇总

| # | 依赖 | 许可证 | 体积 | 风险 | 状态 |
|---|------|--------|------|------|------|
| 7 | `paddlepaddle` (CPU) | Apache 2.0 | ~300-400MB | 低 | ⏳ 待 Codex 批准 |
| 8 | `paddleocr` | Apache 2.0 | ~5-10MB + 模型 ~50-100MB | 低 | ⏳ 待 Codex 批准 |
| 9 | `opencv-python-headless` | Apache 2.0 | ~30-50MB | 低 | ⏳ 待 Codex 批准 |
| 10 | `python-multipart` | Apache 2.0 | ~0.1MB | 低 | ⏳ 待 Codex 批准 |

**备注：**
- PaddleOCR 模型文件由初始化脚本（`scripts/init_paddleocr_models.py`）在开发准备阶段下载到本地缓存目录（约 50-100MB），只需执行一次。运行时加载 PaddleOCR **禁用自动下载**，仅使用已缓存模型；缓存缺失时返回 `OCR_MODEL_NOT_FOUND` 而非触发联网
- 以上依赖仅安装在本地服务 Python 环境（`desktop-app/local-service/`），不涉及云端后台
- **所有依赖状态为"待 Codex 批准"，在 Codex 明确批准前不安装**

## 验收标准

### 本地 OCR 引擎
- ✅ PaddleOCR wrapper 参数白名单生效（拒绝白名单外参数）
- ✅ 文件类型校验生效（拒绝非白名单扩展名 / MIME 类型）
- ✅ 文件大小校验生效（拒绝超大文件）
- ✅ 超时控制生效（超时返回统一错误码）
- ✅ 路径限制生效（拒绝路径穿越）
- ✅ 返回结构符合 `docs/10-local-ai-tools-guide.md` 规范
- ✅ 错误不泄露内部堆栈

### 本地 OCR API
- ✅ `POST /local/ocr` 接受图片文件，返回 `{success, data, error, request_id}`
- ✅ `GET /local/ocr/health` 返回 OCR 引擎就绪状态
- ✅ 不接受非图片文件
- ✅ 不接受超大文件（> 50MB 默认）
- ✅ 响应格式统一

### 桌面端 UI
- ✅ 用户可以通过文件选择器选择图片
- ✅ 用户可以通过拖拽上传图片
- ✅ 图片预览正确显示
- ✅ 点击 OCR 按钮触发识别
- ✅ 识别过程显示 loading 状态
- ✅ 识别结果正确展示全文 + 文本块列表
- ✅ 错误状态有用户友好提示
- ✅ 不支持的文件类型给出明确提示

### OCR 历史
- ✅ OCR 结果存入本地 SQLite
- ✅ 历史列表按时间倒序显示
- ✅ 支持分页加载
- ✅ 可查看历史 OCR 详情
- ✅ 不存储明文敏感信息

### 安全
- ✅ 本地不保存明文 Token / API Key
- ✅ 本地服务仅监听 127.0.0.1
- ✅ 所有 API 响应遵循统一结构 `{success, data, error, request_id}`
- ✅ 本地服务不提供任意命令执行能力
- ✅ PaddleOCR wrapper 不存在命令注入风险
- ✅ 日志不泄露文件内容
- ✅ 不向云端发送任何 OCR 内容或用户文件路径
- ✅ OCR 历史不保存用户原始绝对路径
- ✅ OCR 历史不保存包含用户名/客户名的目录路径
- ✅ 图片预览只引用应用沙箱内副本或临时文件

## 测试方式

必须至少提供：

### 本地服务测试
- PaddleOCR wrapper 单元测试（≥ 5 个）：
  - 参数白名单校验
  - 文件扩展名校验
  - 文件 MIME 类型校验
  - 文件大小超限拒绝
  - 超时控制
  - 错误码映射
  - 路径穿越拒绝
- 本地 OCR API 端点测试（≥ 4 个）：
  - 正常图片上传 → 返回 OCR 结果
  - 非图片文件上传 → 422 拒绝
  - 超大文件上传 → 413/422 拒绝
  - Health check 正常响应
- OCR 历史 API 测试（≥ 3 个）：
  - 保存并查询历史
  - 分页加载
  - 单条详情查询

### 测试目标
- ≥ 12 个测试用例
- 100% 通过
- 全部在本地运行（不依赖云端服务、不依赖 PostgreSQL）

## 是否允许新增依赖

是。4 个依赖 **待 Codex 批准**（批准前不安装）：

| # | 依赖 | 许可证 | 状态 |
|---|------|--------|------|
| 7 | `paddlepaddle` (CPU) | Apache 2.0 | ⏳ 待 Codex 批准 |
| 8 | `paddleocr` | Apache 2.0 | ⏳ 待 Codex 批准 |
| 9 | `opencv-python-headless` | Apache 2.0 | ⏳ 待 Codex 批准 |
| 10 | `python-multipart` | Apache 2.0 | ⏳ 待 Codex 批准 |

均为本地服务依赖，不影响云端后台。

## 是否涉及重大变更

是（仅限 `desktop-app/` 本地范围，不涉及 cloud-backend / PostgreSQL）。

原因：Task-04 新建本地 SQLite 表 `ocr_history`（DDL 参见 §4），按项目规则 `CODEX.md:34` "修改数据库表结构" 属于重大变更。但本变更严格限定在桌面端本地 SQLite，**不修改** cloud-backend PostgreSQL 的任何表结构、Model、或 DDL 文件。

| 维度 | 说明 |
|------|------|
| 变更类型 | 新建本地 SQLite 表（`ocr_history`），不修改已有表 |
| 影响范围 | `desktop-app/local-service/ocr_history.db`（SQLite 文件，首次运行时自动创建） |
| 是否影响云端 | 否。cloud-backend PostgreSQL 表结构、DDL、Model 均不变 |
| 是否影响 API 契约 | 否。`docs/05-api-contract.md` 不变 |
| 是否影响 Provider 接口 | 否 |
| 是否影响授权/Token | 否 |
| 是否需要数据库迁移 | 否。本地 SQLite 为新建，不涉及 Alembic/migration 工具 |

风险点：
- PaddleOCR 依赖体积大（~400MB），首次安装耗时长
- 本地 SQLite schema 设计影响后续 OCR 功能扩展
- 本地服务与桌面端通信依赖 127.0.0.1:9100，端口冲突需处理
- OCR 模型首次下载需联网（约 50-100MB），需通过初始化脚本处理下载失败；运行时模型缓存就绪后不需要网络

影响范围（全部在 `desktop-app/` 内）：
- `desktop-app/local-service/` — 本地 OCR 服务（wrapper、路由、历史、入口）
- `desktop-app/src/` — 桌面端 UI（OCR 工作台、历史列表、API 调用层）
- `desktop-app/tests/` — 本地测试

回滚方案：
- 通过 Git 分支回滚（当前在 `feature/sprint-01-ocr-minimal`）
- 本地 SQLite 为新建，无数据迁移需求
- 不影响 `cloud-backend/` 任何代码

是否兼容旧版本：是（无旧版本）。

是否需要数据库迁移：否（本地 SQLite 为新建，不涉及云端 PostgreSQL）。

## 给 Codex Review 的审查指令

请审查 Task-04 OCR 最小闭环任务单（第 4 轮，已按第 1-3 轮 Review 意见修复，本轮重点修复第 4 轮阻断问题）。

### 第 4 轮修复内容

1. **阻断 #1 修复**：已添加 `desktop-app/local-service/scripts/init_paddleocr_models.py` 到允许文件列表（§允许修改哪些文件/本地服务）
2. **阻断 #2 修复**：已将"是否涉及重大变更"改为"是（仅限 desktop-app 本地 SQLite，不涉及 cloud-backend / PostgreSQL）"，并附详细维度说明表
3. **高风险修复**：已在 §3 本地服务入口更新中明确"运行时初始化 PaddleOCR 必须禁用自动下载"，模型下载仅限初始化脚本执行
4. **中低风险修复**：已为 `desktop-app/package.json` 添加"允许调整构建配置，但不新增 npm 依赖"说明

### 重点检查

1. ✅ 任务范围是否仅限本地 OCR（不涉及 cloud-backend、usage_events、provider_call_log、扣费/支付）
2. ✅ "允许修改哪些文件" 是否包含初始化脚本路径（应包含：`scripts/init_paddleocr_models.py`）
3. ✅ "允许修改哪些文件" 是否包含任何 cloud-backend 文件（不应包含）
4. ✅ "禁止修改哪些文件" 是否覆盖了 cloud-backend 全目录
5. ✅ PaddleOCR 模型缓存策略是否解决了"离线运行"与"首次下载"的冲突
6. ✅ §3 是否明确运行时禁用自动下载、仅初始化脚本可下载模型
7. ✅ PaddleOCR wrapper 安全规则是否完整（参数白名单、文件校验、超时、路径限制、命令注入防护）
8. ✅ 本地服务是否仅监听 127.0.0.1（不暴露公网）
9. ✅ 新增依赖许可证和体积是否可接受
10. ✅ 是否存在前端直连第三方 AI API 的设计（不应存在）
11. ✅ OCR 内容全文是否上报到云端（不应上报，Task-04 纯本地）
12. ✅ 本地 SQLite 是否存储明文敏感信息、用户绝对路径、包含 PII 的目录路径
13. ✅ "是否涉及重大变更"口径是否正确（是，但仅限 local SQLite，不涉及 cloud-backend）
14. ✅ 任务单"本次不开发什么"是否覆盖了 BACKLOG / P1 / FUTURE / 云端相关功能

输出：
- 任务单结构完整性
- 范围越界检查
- 安全风险检查
- 依赖风险检查
- 验收标准完整性
- 任务单是否批准
- 修改建议（如有）
