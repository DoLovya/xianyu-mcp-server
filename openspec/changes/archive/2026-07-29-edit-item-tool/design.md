## Context

闲鱼商品编辑链路由三个底层 API 组成：
1. `get_item_edit_detail(item_id)` — 获取商品的完整编辑详情（包含所有当前字段值）
2. `build_reshelf_payload(edit_detail)` — 基于编辑详情构造重发布/编辑 payload
3. `edit_item(payload)` — 提交编辑请求

当前 MCP 层只暴露了 `get_item_edit_detail` 作为只读工具（已实现），未开放编辑链路。
编辑接口仅对实体商品有效，虚拟商品无法通过此接口修改。

## Goals / Non-Goals

**Goals:**
- 提供一个 `edit_item` MCP 工具，让客户端能编辑商品的核心字段（标题、价格、描述、图片、运费等）
- 封装复杂的 payload 构造逻辑，提供简单易用的接口

**Non-Goals:**
- 不包含"全新发布商品"能力（那是另一条链路）
- 不修改底层 API 逻辑

## Decisions

**决策 1：提供两层接口 — 简化版 + 原始版**
- 简化版：客户端只传需要修改的字段，自动补全其余字段（通过先调 `get_item_edit_detail` 获取当前值）
- 原始版：客户端直接传完整 payload，跳过详情读取
- 原因：纯低级封装会让客户端承担过多 payload 构造负担

**决策 2：保留 `reshelf_item` 与 `edit_item` 并存**
- `reshelf_item` 专门用于下架后重新上架
- `edit_item` 用于编辑已在线商品
- 两者底层都走 `edit_item` API，但前置逻辑不同

## Risks / Trade-offs

- **编辑对虚拟商品无效**：接口本身会返回错误，工具不做前置过滤，由调用方自行控制
- **payload 结构可能随闲鱼版本变化**：`build_reshelf_payload` 中的字段列表需要定期维护
