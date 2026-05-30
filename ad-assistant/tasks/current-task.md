# 当前任务：Sprint-01 基础闭环任务单

## 状态

MVP_REQUIRED

## Sprint-01 开发计划

Sprint-01 只允许包含：
- 项目基础结构
- 登录授权最小闭环
- OCR 最小闭环
- OCR 历史记录
- 使用统计基础表
- provider_call_log 表

## 本次只开发什么

1. 建立 Monorepo 基础工程结构。
2. 建立桌面端、云端后台、官网、shared 的最小项目骨架。
3. 实现登录授权最小闭环。
4. 实现 OCR 最小闭环。
5. 实现桌面端 OCR 历史记录。
6. 设计并实现使用统计基础表。
7. 设计并实现 `provider_call_log` 表。
8. 保证所有云端 AI 调用经过 Provider 层。

## 本次不开发什么

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
- 转矢量业务
- 基础修图业务
- 高级 AI 修图业务
- AI 门头效果图业务
- 支付系统
- 自动更新系统
- 企业后台复杂权限

## 允许修改哪些文件

允许在确认后修改：
- `desktop-app/**`
- `cloud-backend/**`
- `official-website/**`
- `shared/**`
- `tasks/current-task.md`
- 与 Sprint-01 直接相关的文档

## 禁止修改哪些文件

未经用户再次确认，禁止修改：
- API 契约正式文件
- shared DTO 正式文件
- Tauri 权限配置
- 自动更新配置
- Provider 接口定义
- Token 机制
- 支付逻辑
- 与 Sprint-01 无关的模块

## 验收标准

登录授权：
- 用户可以提交账号密码登录。
- 云端返回短期 access token 和 refresh token。
- 设备指纹提交到云端。
- 云端能判断设备绑定状态。
- 客户端不保存明文 Token。

OCR：
- 用户可以上传一张图片。
- 用户可以点击 OCR。
- OCR 返回文本和分块结果。
- OCR 结果能在桌面端展示。
- OCR 结果能保存到本地历史。

使用统计：
- OCR 执行后写入使用统计事件。
- 统计事件包含 user_id、device_id、feature、event_type、created_at。

Provider 日志：
- 云端 Provider 调用必须写入 `provider_call_log`。
- 日志包含 provider、model、estimated_cost、credits_charged、status、request_id。

安全：
- 前端没有第三方 AI API Key。
- 前端不直接调用第三方 AI API。
- 客户端不直接扣点。
- 客户端不决定套餐。

## 测试方式

必须至少提供：
- 云端 Auth API 测试
- 设备绑定测试
- OCR API 或本地 OCR 服务测试
- OCR 历史记录写入测试
- usage_events 写入测试
- provider_call_log 写入测试
- 前端无 API Key 泄露检查

## 是否允许新增依赖

默认不允许。

如果必须新增依赖，必须先输出依赖名称、用途、许可证、体积影响、安全风险，等待用户确认。

任务 1 的脚手架例外：
- 允许安装或生成项目基础骨架所必需的依赖：Tauri 2、Vite、Vue 3、TypeScript、Pinia、FastAPI、Next.js、Tailwind CSS。
- 这些依赖仅可用于初始化 `desktop-app`、`cloud-backend`、`official-website` 的最小工程骨架。
- 不允许借脚手架初始化之名引入业务 SDK、AI Provider SDK、OCR 工具、支付 SDK、数据库驱动、ORM、迁移工具或后台管理框架。
- 如脚手架命令默认生成额外依赖，执行者必须在完成输出中列出依赖名称和用途，供 Codex Review。

## 是否涉及重大变更

是。

原因：
Sprint-01 会建立项目骨架、数据库基础表、登录授权最小闭环、Provider 日志表。

风险点：
- 数据库结构一旦落地会影响后续迁移。
- 登录和 Token 机制影响安全边界。
- Provider 日志结构影响成本统计。
- 目录结构影响后续模块组织。

影响范围：
- `desktop-app`
- `cloud-backend`
- `shared`
- 数据库迁移
- 登录授权
- Provider 调用链路

回滚方案：
- 通过 Git 分支回滚 Sprint-01 改动。
- 数据库迁移必须提供 downgrade 或手动回滚说明。
- 未发布前可重建开发库。

是否兼容旧版本：
当前无旧版本。

是否需要数据库迁移：
需要。

## 给 Claude Code + DeepSeek 的第一条开发任务

任务名称：建立 Sprint-01 项目基础结构和最小模块目录骨架。

执行前必须读取：
- `README.md`
- `CODEX.md`
- `CLAUDE.md`
- `docs/02-system-architecture.md`
- `docs/05-api-contract.md`
- `docs/06-provider-architecture.md`
- `docs/08-security-and-anti-crack.md`
- `docs/12-database-design.md`
- `tasks/current-task.md`

本次只允许：
1. 初始化 `desktop-app`、`cloud-backend`、`official-website`、`shared` 的最小工程骨架。
2. 为云端后台预留 Auth、Device、OCR、Usage、Credit、Provider Log 模块目录。
3. 为桌面端预留登录页、OCR 页面、本地历史模块目录。
4. 为 shared 预留 OpenAPI、DTO、错误码、常量目录。
5. 输出数据库迁移方案草案，但不要在未确认前执行真实数据库迁移。
6. 使用脚手架基础依赖初始化工程，但不得实现登录、OCR、扣费、Provider 调用等业务逻辑。

本次禁止：
- 实现登录 Auth API 业务逻辑。
- 实现设备绑定业务逻辑。
- 实现 Token 签发、刷新、存储业务逻辑。
- 实现 OCR 业务逻辑。
- 实现本地 OCR 调用。
- 创建或执行真实数据库迁移。
- 实现未来功能。
- 接入真实第三方 AI API。
- 写入任何真实 API Key。
- 安装业务 SDK、AI Provider SDK、OCR 工具、支付 SDK、数据库驱动、ORM、迁移工具或后台管理框架。
- 修改 Tauri 权限。
- 修改自动更新逻辑。
- 实现支付。
- 实现转矢量、修图、门头效果图。

验收标准：
- 目录结构符合 `docs/03-monorepo-structure.md`。
- 每个子项目有最小 README 说明职责。
- 云端模块目录清晰存在。
- 桌面端模块目录清晰存在。
- shared 目录清晰存在。
- 数据库迁移方案以 Markdown 输出，等待用户确认。
- 依赖清单中只包含任务 1 允许的脚手架基础依赖。
- 没有 Auth、Device、OCR、Credit、Provider 的真实业务实现。
- 没有真实数据库迁移文件被执行。
- 未出现任何业务越界开发。

## 给 Codex Review 的第一条审查指令

请审查 Claude Code + DeepSeek 对 Sprint-01 第一条任务的实现。

重点检查：
1. 是否只建立项目基础结构和最小技术骨架。
2. 是否越界实现未来功能。
3. 是否引入未经确认的新依赖。
4. 是否修改 Tauri 权限、自动更新、Token 机制、Provider 接口。
5. 是否写入 API Key、密钥、明文 Token。
6. 是否提前执行数据库迁移。
7. 是否存在前端直连第三方 AI API 的代码。
8. 是否符合 `tasks/current-task.md` 的允许/禁止范围。

输出：
- 阻断问题
- 高风险问题
- 中低风险问题
- 验收结论
- 下一步建议
