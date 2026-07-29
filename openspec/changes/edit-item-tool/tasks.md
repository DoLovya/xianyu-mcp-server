# Tasks

## 前置条件
实现已完成，端到端测试依赖实体商品：
- 有已上架的实体商品可用于测试编辑功能
- 或通过 MCP 先发布一件实体商品再测试编辑

## 实施任务

- [x] Task 1: 在 `XianYuApiTools` 中新增 `edit_item` 方法
  - 支持快速编辑模式（`item_id` + `overrides`）和直接编辑模式（`item_id` + `payload`）
  - 快速模式内部调用 `get_item_edit_detail` → `build_reshelf_payload` → 覆盖字段 → `edit_item`
  - 直接模式直接调用 `edit_item` 提交 payload
  - 参考现有工具的返回格式（`success`、`item_id`、`api`、`raw`）

- [x] Task 2: 在 `server.py` 中注册 `edit_item` 工具
  - 声明参数：`item_id`（必填）、`payload`（可选，与 overrides 互斥）、`overrides`（可选，与 payload 互斥）
  - 添加工具描述，注明仅对实体商品有效

- [ ] Task 3: 用实体商品手动测试编辑功能
  - 测试快速编辑模式：修改标题和价格
  - 测试直接编辑模式：提交完整 payload
  - 验证响应格式与错误处理
