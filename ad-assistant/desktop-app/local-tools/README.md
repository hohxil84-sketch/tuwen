# Local Tools — CLI 工具封装文档

## Sprint-01 工具状态

| 工具 | 用途 | Sprint-01 状态 |
|------|------|---------------|
| PaddleOCR | OCR 文字识别 | ✅ 允许开发 |

## 封装要求

所有工具通过本地 FastAPI 服务 (`local-service/`) 封装，不直接暴露给前端。

每个工具封装必须：
- 参数白名单
- 文件类型校验（白名单制）
- 文件大小限制
- 路径限制
- 超时控制
- 错误码映射
- 日志脱敏

## 调用方式

```python
# ✅ Correct: parameter list + shell=False
subprocess.run(
    ["tool_name", "--arg", safe_value],
    shell=False, timeout=60, capture_output=True
)

# ❌ Forbidden: string concatenation + shell=True
subprocess.run(f"tool_name --arg {user_input}", shell=True)
```

## 禁止

- 接收任意 shell 命令
- 使用 os.system()
- 暴露公网端口（只监听 127.0.0.1）
- 通用文件系统访问接口
- 绕过云端授权
