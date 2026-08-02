## Why

当前 MCP 具备“商品详情/我的商品列表/发布编辑/会话消息”等能力，但缺少“商品搜索”能力，导致无法在工具侧做系统化的商品调研（关键词检索、排序、筛选、翻页抽样）。

## What Changes

- 增加“商品搜索”能力：基于闲鱼 PC Web 的搜索接口，实现关键词搜索、排序、翻页（筛选字段先以透传结构承载）。
- 增加抓包证据文档：沉淀搜索相关接口的 URL、参数结构、响应结构（脱敏），作为后续实现与回归依据。
- （可选）增加“搜索联想/遮罩”能力：用于搜索词建议与快速探索。

## Capabilities

### New Capabilities

- `item-search`: 提供商品搜索（关键词/排序/翻页/筛选透传）能力，并在 MCP 层暴露 `search_items` 工具用于商品调研。

### Modified Capabilities

- （无）

## Impact

- `third_party/pyxianyu`：新增 SearchApi（或扩展现有 API 集合）以调用 `mtop.taobao.idlemtopsearch.pc.search`。
- `src/xianyu_mcp`：新增 MCP 工具 `search_items`，并通过 guardrails 按读操作限速。
- `.trae/documents`：补充“商品搜索抓包报告”，作为接口证据与字段基线。
