# Shared — 跨项目共享层

## 职责

- OpenAPI 规范（API 契约的权威来源）
- DTO 定义（数据传输对象）
- TypeScript 类型（由 OpenAPI 生成或手动同步）
- 错误码（统一错误码枚举）
- 常量（共享常量定义）
- SDK（客户端 SDK）

## 原则

- API 契约以 `openapi/` 为准
- 前后端类型必须同步
- 修改 shared 文件属于重大变更，必须先确认
- 所有响应遵循统一结构 `{ success, data, error, request_id }`

## Sprint-01 状态

当前为最小工程骨架。所有目录已预留，**尚未定义具体契约文件**。
