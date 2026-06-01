# Current Task: S04-T03 — Local OCR History Cleanup / 隐私清理

## 状态

`IN_PROGRESS` — 实施中。

## 背景

Sprint-01 Task-04 完成了 OCR 历史记录的 SQLite 持久化存储（`ocr_history` 表）和沙箱图片副本（`ocr_images/` 目录），但：

- 用户无法删除单条 OCR 历史记录
- 用户无法清空全部历史记录
- 沙箱图片副本永不清理（累积磁盘占用）
- 这是 Sprint-01 Summary 明确记录为已知残余风险（含用户敏感 OCR 内容和图片元数据）

本任务补齐本地 OCR 历史的删除/清空能力和相关的沙箱文件清理。

## 本次只开发什么

### Part A: 后端删除函数 (history.py)

- `delete_history_by_id(record_id: str) -> Optional[str]` — 先 SELECT local_copy_path，再 DELETE，返回路径供清理
- `clear_all_history() -> tuple[int, list[Optional[str]]]` — SELECT 全部 local_copy_path，再 DELETE ALL，返回 (count, paths)

### Part B: 后端 DELETE 端点 (routes/ocr.py)

- `DELETE /local/ocr/history/{record_id}` — 单条删除 + 沙箱文件清理，不存在返回 404
- `DELETE /local/ocr/history` — 清空全部 + 逐个沙箱文件清理，返回 deleted_count

### Part C: 前端服务层 (ocrService.ts)

- `deleteHistoryRecord(id: string)` — 调用 DELETE 端点
- `clearAllHistory()` — 调用清空端点

### Part D: 前端 UI (HistoryPage.vue)

- 顶部工具栏：「清空全部」按钮
- 每条记录卡片右上角：× 删除按钮 + 内联确认条
- 清空全部确认弹窗（复用已有 modal 样式）
- isDeleting / pendingDeleteId / showClearConfirm 状态管理
- 删除后刷新列表，末页最后一条自动回退

## 本次不开发什么

- 不自动清理/TTL 过期（需产品决策）
- 不多选批量删除
- 不撤销/回收站
- 不涉及云端 API
- 不新增依赖
- 不修改 DDL/Schema
- 不使用 window.confirm()

## 允许修改哪些文件

### 后端
- `desktop-app/local-service/history.py` — 新增 2 个函数
- `desktop-app/local-service/routes/ocr.py` — 新增 2 个 DELETE 端点 + 更新 import/docstring
- `desktop-app/local-service/tests/test_ocr_history.py` — 新增 TestDeleteHistory（7 tests）
- `desktop-app/local-service/tests/test_ocr_api.py` — 新增 TestDeleteHistoryEndpoints（6 tests）

### 前端
- `desktop-app/src/services/ocrService.ts` — 新增 2 个函数
- `desktop-app/src/pages/HistoryPage.vue` — 工具栏 + 删除按钮 + 确认 UI + CSS

### 文档
- `tasks/current-task.md` — 实现记录
- `PROGRESS.md` — 进度记录

## 禁止修改哪些文件

- 不修改 shared/、cloud-backend/
- 不修改 desktop-app/src-tauri/
- 不修改 desktop-app/package.json
- 不修改 local-service/main.py
- 不修改 local-service/wrappers/
- 不修改 local-service/requirements.txt

## 验收标准

### Part A
- [ ] `delete_history_by_id()` 删除已存在记录，返回 local_copy_path
- [ ] `delete_history_by_id()` 对不存在的 ID 返回 None
- [ ] `clear_all_history()` 返回 (count, paths)，清空全部

### Part B
- [ ] `DELETE /local/ocr/history/{id}` 返回 200 + deleted_id
- [ ] `DELETE /local/ocr/history/{id}` 不存在时返回 404 + NOT_FOUND
- [ ] `DELETE /local/ocr/history` 返回 200 + deleted_count
- [ ] 删除时清理沙箱图片副本
- [ ] 遵循统一响应格式

### Part C
- [ ] `deleteHistoryRecord()` 调用正确端点
- [ ] `clearAllHistory()` 调用正确端点

### Part D
- [ ] 每条历史记录有删除按钮，点击后出现确认条
- [ ] 清空全部按钮打开确认弹窗
- [ ] 删除成功后刷新列表
- [ ] 删除失败显示中文错误
- [ ] 本地服务不可用时显示连接失败提示
- [ ] 按钮在删除过程中禁用

### 通用
- [ ] 所有新功能有测试覆盖
- [ ] 现有回归测试全部通过
- [ ] 不新增依赖
- [ ] 不修改 DDL

## 测试方式

```bash
# 后端单元测试
cd ad-assistant/desktop-app/local-service
python -m pytest tests/test_ocr_history.py -v -x

# 后端 API 集成测试
python -m pytest tests/test_ocr_api.py -v -x

# 全量
python -m pytest tests/ -v -x

# 桌面端构建
cd ad-assistant/desktop-app
npm run build
```

## 是否允许新增依赖

不允许。

## 是否涉及重大变更

**否** — 纯增量功能，不修改已有接口签名，不涉及数据库 schema 变更。

## 安全检查

- [ ] 不存储 secrets/密钥/Token
- [ ] 不修改云端 API
- [ ] 沙箱文件清理仅限 `ocr_images/` 目录下文件
- [ ] 不删除其他用户数据

## 风险点

1. **沙箱文件清理失败不影响 DB 删除**：先 DB 后文件，文件清理失败只是遗留孤儿文件
2. **FastAPI 路由冲突**：`DELETE /local/ocr/history/{record_id}` 和 `DELETE /local/ocr/history` 路径签名不同，FastAPI 正确区分

---

## 实现记录 (2026-06-02)

### 修改文件

**后端（修改）**
- `desktop-app/local-service/history.py` — + `delete_history_by_id()` + `clear_all_history()`
- `desktop-app/local-service/routes/ocr.py` — + `DELETE /local/ocr/history/{id}` + `DELETE /local/ocr/history`
- `desktop-app/local-service/tests/test_ocr_history.py` — + `TestDeleteHistory` (7 tests)
- `desktop-app/local-service/tests/test_ocr_api.py` — + `TestDeleteHistoryEndpoints` (6 tests)

**前端（修改）**
- `desktop-app/src/services/ocrService.ts` — + `deleteHistoryRecord()` + `clearAllHistory()`
- `desktop-app/src/pages/HistoryPage.vue` — + 工具栏 + 删除按钮 + 内联确认条 + 清空确认弹窗

**文档**
- `tasks/current-task.md` — 任务单 + 实现记录

### 实现内容

**Part A: history.py — 全部完成**
- `delete_history_by_id(record_id) -> Optional[str]`: SELECT 后 DELETE，返回 local_copy_path 供沙箱清理
- `clear_all_history() -> tuple[int, list[Optional[str]]]`: 收集全部路径后 DELETE ALL

**Part B: routes/ocr.py — 全部完成**
- `DELETE /local/ocr/history/{record_id}`: 删除单条 + 清理沙箱文件，不存在返回 404
- `DELETE /local/ocr/history`: 清空全部 + 逐个清理沙箱文件，返回 deleted_count
- 统一响应格式: `{success, data, error, request_id}`
- 已有 `_cleanup_sandbox_copy()` 复用，docstring 更新

**Part C: ocrService.ts — 全部完成**
- `deleteHistoryRecord(id)`: 调用 DELETE /local/ocr/history/{id}
- `clearAllHistory()`: 调用 DELETE /local/ocr/history
- 复用 request<T>() helper (AbortController 30s timeout)

**Part D: HistoryPage.vue — 全部完成**
- 顶部工具栏: 标题 + "清空全部" 按钮（非空列表时显示）
- 每条记录: × 删除按钮 + 内联确认条（确认删除 / 取消）
- 清空全部确认弹窗: 显示记录数量 + 不可撤销提示
- 状态管理: isDeleting / pendingDeleteId / showClearConfirm
- 错误处理: 删除/清空失败显示中文错误
- 删除后刷新: 末页最后一条自动回退
- 清空后: selectedId + selectedRecord 重置为 null

### 未实现内容

- 不涉及（所有计划内容已实现）

### 自审结论

- 只实现了 tasks/current-task.md 允许的内容: 是
- 只修改了 allowed files: 是
- 未混入无关文件: 是
- 未新增依赖: 是
- 未触碰高风险边界: 是（纯本地服务增量功能）
- 未存储 secrets: 是
- 测试覆盖: 13 个新测试全部通过
- 回归测试: 全部通过（42 tests total）
- 构建: npm run build 通过（65 modules, 0 errors）
- PROGRESS.md: 待更新

### 测试结果

```
# 后端单元测试
cd desktop-app/local-service
python -m pytest tests/test_ocr_history.py -v -x
19 passed

# 后端 API 集成测试
python -m pytest tests/test_ocr_api.py -v -x
23 passed

# 全量
python -m pytest tests/ -v -x
42 passed

# 桌面端构建
npm run build
65 modules, 0 errors
```

### 是否触发高风险暂停规则

否。

### 风险和回滚方式

1. **孤儿沙箱文件**: 删除时先清 DB 后清文件。文件清理失败仅留孤儿文件在 `ocr_images/`，不影响 DB 一致性。
2. **清空全部后无撤销**: 设计决策为永久删除，确认弹窗有明确提示。
3. **回滚方式**: revert 对应提交，恢复无删除能力的历史页面。

