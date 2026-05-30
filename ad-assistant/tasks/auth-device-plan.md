# Sprint-01 Task-02: Auth / Device 方案

> ⚠️ **方案文档 — 不包含任何业务代码实现。** 所有依赖需经用户确认后方可安装，所有数据库变更需经用户确认后方可执行。

---

## 关联文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 主方案 | [auth-device-plan.md](../cloud-backend/docs/auth-device-plan.md) | Auth/Device 流程、数据库、测试计划 |
| 依赖申请 | [dependency-request.md](../cloud-backend/docs/dependency-request.md) | 需新增的后端依赖逐项分析 |
| API 草案 | [api-draft-auth-device.md](../cloud-backend/docs/api-draft-auth-device.md) | 5 个端点的请求/响应草案 |

---

## 待用户确认事项

1. **数据库选型**：PostgreSQL 还是 MySQL？（方案推荐 PostgreSQL）
2. **主键策略**：UUID v4 / UUID v7 / ULID？
3. **依赖批准**：`python-jose` + `passlib[bcrypt]` 是否可以安装？
4. **设备数量上限**：每用户允许绑定多少台设备？建议 3 台。
5. **refresh token 有效期**：建议 30 天，是否需要调整？
6. **access token 有效期**：建议 30 分钟，是否需要调整？

以上事项确认后方可进入 Task-03 实现。
