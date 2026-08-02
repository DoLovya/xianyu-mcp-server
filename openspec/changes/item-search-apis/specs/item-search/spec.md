# item-search Specification

## Purpose

为“商品调研”提供可编程的商品搜索能力：通过关键词检索并支持排序与翻页抽样，输出原始响应与最小可用的商品列表摘要。

## ADDED Requirements

### Requirement: 提供商品搜索 MCP 工具

系统 SHALL 提供 MCP 工具 `search_items`，用于按关键词在闲鱼 PC Web 搜索并返回结果。

#### Scenario: 基础关键词搜索

- **WHEN** 调用 `search_items`，提供 `keyword="iPhone 13"`
- **THEN** 系统调用 `mtop.taobao.idlemtopsearch.pc.search`
- **THEN** 系统返回 `success=true` 且包含 `raw`（原始响应）与 `items`（精简列表，若可提取）

#### Scenario: 翻页搜索

- **WHEN** 调用 `search_items`，提供 `keyword="iPhone 13"` 且 `page_number=2`
- **THEN** 系统将请求中的 `pageNumber` 设置为 2
- **THEN** 返回结果对应第 2 页内容

#### Scenario: 排序（最新）

- **WHEN** 调用 `search_items`，提供 `keyword="iPhone 13"` 且 `sort_field="create"`、`sort_value="desc"`
- **THEN** 系统将请求中的 `sortField/sortValue` 传入搜索请求

### Requirement: 响应格式

`search_items` 的响应 SHALL 包含以下字段：

- `success` (bool)
- `api` (string)：固定为 `mtop.taobao.idlemtopsearch.pc.search`
- `keyword` (string)
- `page_number` (int)
- `rows_per_page` (int)
- `items` (array)：可选精简列表；提取失败时可返回空数组
- `raw` (object)：闲鱼接口原始响应

#### Scenario: 提取商品摘要字段

- **WHEN** `raw.data.resultList` 中存在商品数据
- **THEN** 系统尽力提取每个商品的 `item_id/title/price/pic_url/area/user_nick_name`
- **THEN** 缺失字段 SHALL 不导致工具报错

### Requirement: 依赖条件与错误

- 系统 SHALL 依赖 `_m_h5_tk` cookie 以生成 MTop 签名。

#### Scenario: 缺少 _m_h5_tk

- **WHEN** 服务端未配置或无法读取 `_m_h5_tk` cookie
- **THEN** 系统返回错误，提示缺少签名所需 cookie

### Requirement: Respect read guardrails

搜索操作 SHALL 被视为读操作并通过 read guardrails 执行，以限制频率并降低风控风险。

#### Scenario: 搜索使用读护栏

- **WHEN** `search_items` 被调用
- **THEN** 系统通过 read guardrails 执行该请求，而非 write guardrails
