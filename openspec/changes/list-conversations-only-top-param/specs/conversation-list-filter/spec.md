## ADDED Requirements

### Requirement: list_conversations 支持 only_top 参数
`list_conversations` MCP Tool 及底层业务方法 SHALL 接收布尔参数 `only_top`，默认值为 `False`。当未显式传入时，行为 SHALL 与未引入该参数前的版本完全一致。

#### Scenario: 不传 only_top 时完全兼容旧行为
- **WHEN** 调用方调用 `list_conversations(max_items=50, include_hidden=False)` 且未指定 `only_top`
- **THEN** 返回结果 SHALL 与旧版本相同：包含所有可见会话，过滤顺序、返回字段（除新增的 `top_count` 外）均不变

#### Scenario: only_top 默认为 False
- **WHEN** 调用方调用 `list_conversations()`（无任何参数）
- **THEN** `only_top` SHALL 被视为 `False`，返回全部可见会话

### Requirement: only_top=True 时仅返回置顶会话
当 `only_top=True` 时，返回的 `conversations` 数组 SHALL 仅包含 `is_top=true` 的条目（且受 `include_hidden` 影响）。

#### Scenario: only_top=True 且 include_hidden=False（默认）
- **WHEN** 调用方调用 `list_conversations(only_top=True)`
- **THEN** 返回的 `conversations` 数组中每一项的 `is_top` SHALL 均为 `true`
- **AND** 所有条目的 `visible` SHALL 均为 `true`

#### Scenario: only_top=True 且 include_hidden=True
- **WHEN** 调用方调用 `list_conversations(only_top=True, include_hidden=True)`
- **THEN** 返回的 `conversations` 数组中每一项的 `is_top` SHALL 均为 `true`
- **AND** 可同时包含 `visible=false` 的置顶隐藏会话

#### Scenario: 不存在置顶会话时返回空列表
- **WHEN** 账号当前没有任何置顶会话，且调用方调用 `list_conversations(only_top=True)`
- **THEN** 返回的 `count` SHALL 为 0
- **AND** `conversations` SHALL 为空数组

### Requirement: 返回结果包含 top_count 字段
`list_conversations` 返回的 JSON SHALL 包含整型字段 `top_count`，用于标识置顶会话的数量。

#### Scenario: only_top=False 时 top_count 为置顶总数
- **WHEN** 调用方调用 `list_conversations(only_top=False)` 且可见结果中有 3 个置顶会话
- **THEN** 返回的 `top_count` SHALL 等于 3
- **AND** `count` SHALL 为所有可见会话数（置顶与非置顶之和）

#### Scenario: only_top=True 时 top_count 等于 count
- **WHEN** 调用方调用 `list_conversations(only_top=True)` 且返回 5 个置顶会话
- **THEN** 返回的 `top_count` SHALL 等于 `count`（均为 5）

### Requirement: only_top 可与 max_items 组合
当同时指定 `only_top=True` 与 `max_items=N` 时，最终结果 SHALL 先按过滤条件（可见性 + 置顶）筛选，再按 `modify_time` 倒序取最多 `N` 条（保持原有排序不变）。

#### Scenario: only_top + max_items 组合截断
- **WHEN** 账号共有 7 个置顶会话，且调用方调用 `list_conversations(only_top=True, max_items=5)`
- **THEN** 返回的 `count` SHALL 为 5
- **AND** `top_count` SHALL 为 5
- **AND** 返回的 5 个会话 SHALL 是按 `modify_time` 倒序的前 5 个置顶会话

### Requirement: 归一化结构 is_top 字段保持布尔语义
`_normalize_conversation` 返回的 `is_top` 字段 SHALL 继续由服务端 `topRank` 非零转布尔，取值仅为 `true`/`false`。

#### Scenario: topRank > 0 视为置顶
- **WHEN** 原始 user_conversation 的 `topRank` 字段为非零整数
- **THEN** 归一化后的 `is_top` SHALL 为 `true`

#### Scenario: topRank = 0 或缺失视为非置顶
- **WHEN** 原始 user_conversation 的 `topRank` 字段为 0 或不存在
- **THEN** 归一化后的 `is_top` SHALL 为 `false`
