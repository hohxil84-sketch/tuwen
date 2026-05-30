# 10 本地 AI 工具指南

## MVP 工具

MVP 优先工具：
- PaddleOCR：OCR

Sprint-01 只允许使用 OCR 最小闭环。

## 工具封装原则

每个本地工具必须通过本地 FastAPI 服务封装。

本地服务 API 必须：
- 参数白名单
- 文件类型校验
- 文件大小限制
- 超时控制
- 错误码映射
- 日志脱敏

## 禁止

禁止：
- 接收任意 shell 命令
- 拼接未校验命令参数
- 处理未限制路径的文件
- 访问用户未选择的文件
- 暴露公网端口
- 绕过云端授权执行高级能力

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

## BACKLOG 工具

以下工具后续再评估：
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

