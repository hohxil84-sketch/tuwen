# 当前任务：Sprint-01 Task-02 Auth / Device 方案确认

## 状态

MVP_REQUIRED

## 背景

Sprint-01 Task-01 已完成项目基础骨架和校验脚本。

下一步进入登录授权最小闭环前，必须先确认 Auth / Device / Token / 数据库迁移方案，因为这些属于安全边界和重大变更。

本任务只允许输出方案和依赖申请，不允许实现业务逻辑。

## 本次只开发什么

1. 梳理云端 Auth / Device 最小闭环方案。
2. 梳理 access token、refresh token、设备绑定、设备禁用的最小安全流程。
3. 梳理需要新增的后端依赖，并说明用途、许可证、体积影响、安全风险。
4. 梳理数据库迁移计划，明确哪些表属于 Task-02 必需。
5. 输出 API 草案，但不得修改正式 OpenAPI 文件。
6. 输出测试计划，覆盖 Auth API、Device 绑定、Token 刷新、无明文 Token。

## 本次不开发什么

- 不实现 Auth API 业务逻辑。
- 不实现设备绑定业务逻辑。
- 不实现 Token 签发、刷新、撤销代码。
- 不创建真实数据库迁移脚本。
- 不执行数据库迁移。
- 不引入依赖。
- 不修改 `shared/openapi/**` 正式契约。
- 不修改 shared DTO 正式文件。
- 不修改 Tauri 权限。
- 不修改自动更新逻辑。
- 不接入 OCR。
- 不接入第三方 AI API。
- 不实现扣点、支付、套餐最终判定。
- 不实现任何 Sprint-01 以外功能。

## 允许修改哪些文件

本次只允许修改或新增：

- `ad-assistant/tasks/current-task.md`
- `ad-assistant/tasks/auth-device-plan.md`
- `ad-assistant/cloud-backend/docs/auth-device-plan.md`
- `ad-assistant/cloud-backend/docs/dependency-request.md`
- `ad-assistant/cloud-backend/docs/api-draft-auth-device.md`

如果目录不存在，可以创建 `ad-assistant/cloud-backend/docs/`。

## 禁止修改哪些文件

未经用户再次确认，禁止修改：

- `ad-assistant/cloud-backend/app/**`
- `ad-assistant/cloud-backend/migrations/**`
- `ad-assistant/shared/**`
- `ad-assistant/desktop-app/**`
- `ad-assistant/official-website/**`
- `ad-assistant/docs/05-api-contract.md`
- `ad-assistant/docs/12-database-design.md`
- 任何依赖清单，例如 `pyproject.toml`、`package.json`

## 必须输出的方案内容

### 1. Auth / Device 流程

必须说明：

- 登录请求字段
- 设备指纹提交方式
- access token 生命周期
- refresh token 生命周期
- refresh token 存储方式，只允许 hash
- 设备绑定规则
- 设备禁用规则
- logout / revoke 的最小行为
- 失败场景和错误码草案

### 2. 数据库计划

必须说明 Task-02 需要哪些表：

- `users`
- `devices`
- `auth_sessions`
- `risk_logs`

如果需要其他表，必须解释原因并等待用户确认。

### 3. 依赖申请

如需新增依赖，必须逐项说明：

- 依赖名称
- 用途
- 许可证
- 体积影响
- 安全风险
- 是否有替代方案
- 为什么不能先用标准库或现有依赖

禁止直接安装依赖。

### 4. API 草案

只允许写草案文档，不允许改正式 OpenAPI。

至少覆盖：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/devices/bind`
- `GET /api/v1/devices/current`

### 5. 测试计划

必须列出后续实现时需要的测试：

- 登录成功
- 登录失败
- refresh token 刷新成功
- refresh token 失效
- 设备首次绑定
- 设备已禁用
- 不保存明文 Token
- 不泄露 password / token 到日志

## 验收标准

- 只新增方案文档，不写业务代码。
- 没有新增依赖。
- 没有修改正式 API 契约。
- 没有修改数据库迁移脚本。
- 没有修改 Token 实现代码。
- 明确列出依赖申请和风险。
- 明确列出需要用户确认的问题。
- Codex Review 通过后，才能进入 Task-03 实现。

## 给 Claude Code + DeepSeek 的开发指令

请在新分支执行：

```powershell
git switch main
git pull origin main
git switch -c docs/auth-device-plan
```

如果 `main` 尚未包含 Sprint-01 骨架，请先停止并告诉用户“需要先合并 Sprint-01 skeleton PR”。

执行前必须读取：

- `ad-assistant/README.md`
- `ad-assistant/CODEX.md`
- `ad-assistant/CLAUDE.md`
- `ad-assistant/docs/05-api-contract.md`
- `ad-assistant/docs/08-security-and-anti-crack.md`
- `ad-assistant/docs/12-database-design.md`
- `ad-assistant/tasks/current-task.md`

本次只允许新增方案文档，不允许写实现代码。

完成后执行：

```powershell
git status --short --branch
python ad-assistant/scripts/validate-skeleton.py
```

如果验证通过，提交：

```powershell
git add ad-assistant/tasks/current-task.md ad-assistant/tasks/auth-device-plan.md ad-assistant/cloud-backend/docs/auth-device-plan.md ad-assistant/cloud-backend/docs/dependency-request.md ad-assistant/cloud-backend/docs/api-draft-auth-device.md
git commit -m "docs(auth): propose auth device implementation plan"
git push -u origin docs/auth-device-plan
```

完成后把 commit hash、验证结果、需要用户确认的问题发回。

## 给 Codex Review 的审查指令

请审查 Task-02 Auth / Device 方案。

重点检查：

1. 是否只写方案，没有实现业务代码。
2. 是否修改了禁止修改的目录。
3. 是否提出依赖申请而不是直接新增依赖。
4. 是否覆盖 Token、设备绑定、设备禁用、日志脱敏。
5. 是否没有修改正式 OpenAPI 和 shared DTO。
6. 是否没有创建或执行真实数据库迁移。
7. 是否明确列出用户需要确认的问题。

输出：

- 阻断问题
- 高风险问题
- 中低风险问题
- 验收结论
- 下一步建议
