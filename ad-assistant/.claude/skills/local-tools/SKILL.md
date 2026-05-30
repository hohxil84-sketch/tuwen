---
name: local-tools
description: 本地工具封装 Skill — PaddleOCR、vtracer、ImageMagick 的受控封装，禁止任意命令执行。触发时机：封装本地 CLI 工具、编写本地 FastAPI 服务端点、处理文件 I/O、调用图像处理工具时。
---

# 本地工具封装 Skill

## MVP 工具

| 工具 | 用途 | Sprint-01 状态 |
|------|------|---------------|
| PaddleOCR | OCR 文字识别 | ✅ 允许开发 |
| vtracer | 位图转矢量 | ⚠️ Sprint-01 只预留文档 |
| ImageMagick | 图片处理 | ⚠️ Sprint-01 只预留文档 |

Sprint-01 只实现 OCR 最小闭环，vtracer 和 ImageMagick 只能预留目录和文档。

## 封装架构

所有本地工具必须通过 **本地 FastAPI 服务** 封装，不直接暴露给前端。

```text
desktop-app/local-service/
  main.py              # FastAPI 入口，仅监听 127.0.0.1
  routes/
    ocr.py             # OCR 端点
    vector.py           # 矢量化端点（预留）
    image.py            # 图片处理端点（预留）
  wrappers/
    paddleocr.py        # PaddleOCR 封装
    vtracer.py           # vtracer 封装（预留）
    imagemagick.py       # ImageMagick 封装（预留）
```

## 必须遵守的安全规则

### ✅ 每个工具封装必须实现

- **参数白名单** — 只接受预定义的参数，拒绝任意参数透传
- **文件类型校验** — 校验文件扩展名和 MIME 类型，白名单制
- **文件大小限制** — 配置文件大小上限（图片默认 50MB）
- **路径限制** — 只处理指定目录内的文件，拒绝绝对路径遍历
- **超时控制** — 每个操作设置超时（OCR 默认 60s）
- **错误码映射** — 统一错误码，不泄露内部异常
- **日志脱敏** — 不记录文件内容、路径中的用户名等敏感信息

### ❌ 禁止

- 接收任意 shell 命令或 command 参数
- 拼接未校验的字符串到命令行
- 使用 `os.system()`、`subprocess.Popen(shell=True)` 处理用户输入
- 处理用户未选择、不在白名单目录内的文件
- 暴露公网端口（只能监听 `127.0.0.1`）
- 提供通用文件系统访问接口
- 绕过云端授权执行高级能力
- 持有云端 Provider API Key

## OCR 最小返回结构

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

## 本地服务启动规范

- 由 Tauri sidecar 管理启动和生命周期
- 只监听 `127.0.0.1`，随机端口或固定内部端口
- 启动时校验运行环境（Python 版本、依赖完整性）
- 异常退出时自动重启（最多重试 3 次）
- 修改启动方式属于重大变更，必须先确认

## 子进程调用规范

如果必须调用外部 CLI（如 `vtracer`、`magick`）：

```python
# ✅ 正确：使用参数列表，禁用 shell
subprocess.run(
    ["vtracer", "--input", safe_path, "--output", safe_output],
    shell=False,
    timeout=120,
    capture_output=True
)

# ❌ 禁止：字符串拼接 + shell
subprocess.run(f"vtracer --input {user_input}", shell=True)
```

所有子进程调用必须在 wrapper 函数内，接受参数校验后再执行。
