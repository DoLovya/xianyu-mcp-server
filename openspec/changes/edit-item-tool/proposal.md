## Why

`goofish_apis.py` 已实现 `edit_item` 接口，但 MCP 层未暴露此工具。添加后客户端可直接编辑商品信息。

## What Changes

- 新增 `edit_item` MCP 工具，接受商品 ID 和编辑参数
- 封装底层 `get_item_edit_detail` → `build_reshelf_payload` → `edit_item` 的调用链路
- 提供简化版接口（按需修改指定字段 + 自动补全其余字段）
- **已知限制**：编辑接口仅对实体商品（非虚拟商品）有效
- **开发时机**：推迟到有可测试的实体商品上架后再实施

## Capabilities

### New Capabilities
- `item-edit`: 提供编辑已发布商品信息的能力，包括修改标题、价格、描述、图片等字段

### Modified Capabilities
- 无

## Impact

- 代码变更范围：`src/xianyu_mcp/tools/xianyu_api_tools.py`（新增 edit_item 方法）、`src/xianyu_mcp/server.py`（注册新工具）
- 不涉及 API 层改动，直接复用 `goofish_apis.py` 中已有的 `edit_item`
