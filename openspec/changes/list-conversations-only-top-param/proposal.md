## Why

当前 `list_conversations` 接口虽然在每个会话对象中返回了 `is_top` 字段（标识会话是否被置顶），但调用方若想单独获取"置顶会话列表"，必须拉取全部会话后自行过滤。这在会话数量较多时效率较低且调用繁琐。通过在接口层面提供 `only_top` 过滤参数，可直接返回置顶会话，简化上层调用逻辑、减少数据传输量。

## What Changes

- 在 `list_conversations` MCP Tool 及其底层业务方法中新增布尔参数 `only_top`（默认 `False`，保持向后兼容）。
- 当 `only_top=True` 时，返回结果仅包含 `is_top=true` 的会话；当 `only_top=False` 时行为与当前完全一致。
- `only_top` 可与 `include_hidden`、`max_items` 自由组合使用。
- 返回 JSON 中额外增加 `top_count` 字段（当 `only_top=False` 时表示全部结果中的置顶会话数量），便于调用方统计。

## Capabilities

### New Capabilities

- `conversation-list-filter`: 会话列表过滤能力，涵盖 `only_top`、`include_hidden` 等参数的组合过滤逻辑及返回结果的计数字段。

### Modified Capabilities

<!-- 无现有 spec 级别的行为变更，仅新增参数 -->

## Impact

- **MCP Tool 接口**：[server.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/server.py) 中 `list_conversations` 增加 `only_top` 参数声明。
- **业务逻辑**：[xianyu_api_tools.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/tools/xianyu_api_tools.py) 中 `list_conversations` 方法增加过滤条件与返回字段。
- **文档 / 协议**：无外部协议变更，仅 MCP Tool 文档字符串更新。
- **兼容性**：参数默认值为 `False`，对现有调用方完全无影响。
