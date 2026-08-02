## Context

- 目标能力来自闲鱼 PC Web（goofish.com）的可观察网络请求。
- 已抓到核心搜索接口：`mtop.taobao.idlemtopsearch.pc.search`（POST `https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/`）。
- 仓库现状：`third_party/pyxianyu/core/client.py` 已实现 MTop 参数拼装与签名（依赖 `_m_h5_tk` cookie），并已用于商品详情/发布编辑等接口。

## Goals / Non-Goals

**Goals:**

- 在 `third_party/pyxianyu` 内新增一层 SearchApi，复用现有签名与请求封装，提供稳定的 `search` 方法。
- 在 MCP 层新增 `search_items` 工具，满足“商品调研”的最小闭环：关键词 + 分页 + 排序（筛选字段以结构化透传方式承载）。
- 将抓包证据（URL/参数结构/响应结构）以脱敏形式固化到文档，作为变更基线。

**Non-Goals:**

- 不承诺覆盖闲鱼全量筛选项语义（例如“包邮/验货宝/类目”具体枚举），仅提供透传接口以便逐步完善。
- 不在本变更中实现 App 端搜索链路与移动端专属接口。
- 不做高频爬虫/全站抓取能力；只提供受 guardrails 保护的“工具级”查询。

## Decisions

- **调用方式：复用现有 MTop 签名通道**
  - 选择：沿用 `XianyuClient.build_mtop_params` + `post_json` + `ensure_api_success`。
  - 原因：仓库已验证该通道对多条 MTop API 可用；实现成本最低且一致性最好。
- **API 封装层：新增 `SearchApi`**
  - 选择：在 `third_party/pyxianyu/apis/` 新增 `search_api.py`，而不是继续膨胀 `item_api.py`。
  - 原因：职责更清晰，后续可扩展 `search.shade`、`search.activate` 等搜索相关接口。
- **MCP 读写分级：搜索走 read guardrails**
  - 选择：`search_items` 在 `XianyuApiTools` 内通过 `run_read` 执行。
  - 原因：搜索属于读操作，但调用频率可能较高，必须受读限速保护以降低风控风险。
- **输出格式：raw 优先 + 可选精简摘要**
  - 选择：返回原始响应 `raw`（脱敏由调用方承担），同时提供可选 `items` 精简列表（itemId/title/price/picUrl/area/userNickName）。
  - 原因：响应结构复杂且可能变动；raw 便于快速适配，精简字段便于直接用于调研。

## Risks / Trade-offs

- [接口字段变动/AB 实验] → 以抓包文档作为基线；输出 raw；精简字段提取采取“尽力而为”，缺字段不报错。
- [_m_h5_tk 缺失或过期] → 在 client 侧维持现有显式报错行为（缺 token 无法签名）；文档中明确依赖条件。
- [风控/频控] → MCP 层强制走 guardrails read；不暴露并发/批量抓取接口。
