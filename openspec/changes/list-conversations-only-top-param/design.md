## Context

当前 `list_conversations` 能力通过 WebSocket `/r/Conversation/listNewest` 拉取会话列表，并已在归一化结构 `_normalize_single_conversation` / `_normalize_group_conversation` 中将服务端 `topRank` 字段转为布尔 `is_top`。调用方如需获取仅置顶的会话，必须先拉取全部结果再在客户端过滤。本改动在服务端增加过滤参数，使调用更简洁高效。

相关代码位置：
- MCP 入口：[server.py L312-L327](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/server.py#L312-L327)
- 业务方法：[xianyu_api_tools.py L669-L690](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/tools/xianyu_api_tools.py#L669-L690)
- `is_top` 解析：[xianyu_api_tools.py L909](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/tools/xianyu_api_tools.py#L909)、[L933](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/src/xianyu_mcp/tools/xianyu_api_tools.py#L933)

## Goals / Non-Goals

**Goals:**
- 在 `list_conversations` MCP Tool 与底层业务方法中增加 `only_top` 参数（默认 `False`）。
- 当 `only_top=True` 时，仅保留 `is_top=true` 的会话条目。
- 返回结构中增加 `top_count` 字段，便于调用方了解置顶会话总数。
- `only_top` 可与 `include_hidden`、`max_items` 任意组合。
- 完全向后兼容：不传 `only_top` 时行为与当前版本完全一致。

**Non-Goals:**
- 不引入新的 WebSocket 路由或抓包分析；仅复用已有 `topRank → is_top` 的解析结果。
- 不新增独立的 `list_top_conversations` MCP Tool。
- 不改变 `_normalize_conversation` 返回结构中的字段语义（`is_top` 仍为布尔）。
- 不修改其他消息相关接口（`list_conversation_messages`、`send_text_message`、`send_image_message`）。

## Decisions

### D1: 在现有 `list_conversations` 上增加参数，而非新增独立 Tool

**Rationale:**
- 现有接口已完全具备获取置顶所需的 `is_top` 数据，仅差服务端过滤一层。
- 新增参数（默认 `False`）是纯向后兼容的扩展，对现有调用方零影响。
- 调用方可在同一接口内组合 `only_top`、`include_hidden`、`max_items`，API 更统一。

**Alternatives considered:**
- **新增独立 Tool `list_top_conversations`**：语义直观但增加 API 表面积，参数组合（如 `include_hidden`）也需要在新 Tool 中重复声明，维护成本更高。否决。

### D2: 过滤在归一化（`_normalize_conversation`）之后执行，顺序为：可见性过滤 → 置顶过滤

**Rationale:**
- 现有代码 `include_hidden` 的过滤发生在 `summaries` 构造之后。按相同模式追加 `only_top` 过滤，可保持风格一致并便于阅读。
- 先过滤可见性再过滤置顶是自然的语义组合：`only_top=True, include_hidden=False` 表示"可见且置顶"的会话。

### D3: `top_count` 字段定义与计算时机

- 当 `only_top=False` 时：`top_count` = 过滤可见性后的总结果中 `is_top=true` 的数量（让调用方知道"全部结果里有多少个置顶"）。
- 当 `only_top=True` 时：`top_count` = `count`（因为所有返回都是置顶）。
- `raw_count` 保持原语义：WS 返回的原始会话条目数（归一化前）。

## Risks / Trade-offs

- **[风险] 调用方混淆 `count` 与 `top_count`** → 缓解：在 Tool docstring 及返回 JSON 示例中用注释明确两个字段语义。
- **[折中] `only_top` 生效于客户端侧过滤（WS 仍拉取完整列表）** → 本版本不引入新的 WS 路由以避免抓包风险；如后续会话量很大，可再考虑服务端专门接口。当前客户端侧过滤足以满足绝大多数场景。

## Migration Plan

无数据迁移需求。部署即为新版本接口上线；旧调用不传新参数完全不受影响。

## Open Questions

无。
