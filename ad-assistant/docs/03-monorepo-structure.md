# 03 Monorepo 结构

## 建议目录

```text
ad-assistant/
  README.md
  CODEX.md
  CLAUDE.md

  docs/
    01-product-vision.md
    02-system-architecture.md
    03-monorepo-structure.md
    04-tech-stack.md
    05-api-contract.md
    06-provider-architecture.md
    07-ai-cost-control.md
    08-security-and-anti-crack.md
    09-desktop-app-guide.md
    10-local-ai-tools-guide.md
    11-cloud-backend-guide.md
    12-database-design.md
    13-module-roadmap.md
    14-ai-agent-workflow.md
    15-coding-standards.md
    16-git-workflow.md
    17-release-and-update.md
    18-ui-style-guide.md
    19-pricing-and-credit-system.md
    20-agent-git-guardrails.md
    21-ci-postgres-integration-tests.md
    22-provider-mock-foundation.md
    23-mock-ai-api-endpoint.md
    24-credit-system-design.md
    25-desktop-mock-e2e-smoke.md

  desktop-app/
    README.md
    src/
    src-tauri/
    local-service/
    local-tools/
    migrations/
    tests/

  cloud-backend/
    README.md
    app/
      api/
      core/
      models/
      schemas/
      services/
      providers/
      workers/
      admin/
    migrations/
    tests/

  official-website/
    README.md
    app/
    components/
    content/
    public/

  shared/
    README.md
    openapi/
    dto/
    typescript/
    error-codes/
    constants/
    sdk/

  tasks/
    task-template.md
    review-template.md
    current-task.md
```

## 目录职责

`desktop-app/`：
桌面客户端、本地 SQLite、本地 FastAPI 服务、本地 CLI 工具封装。

`cloud-backend/`：
云端 API、授权、设备绑定、Provider、扣费、日志、后台管理。

`official-website/`：
官网、下载页、价格页、教程页、注册入口、SEO 页面。

`shared/`：
OpenAPI、DTO、错误码、常量、TypeScript 类型、SDK。

`tasks/`：
任务单和审查模板。开发只能依据 `tasks/current-task.md`。

## 修改目录规则

修改项目目录结构属于重大变更，必须先让用户确认。

新增业务目录前必须说明：
- 新目录用途
- 所属模块
- 是否影响构建
- 是否影响发布
- 是否影响已有路径引用

