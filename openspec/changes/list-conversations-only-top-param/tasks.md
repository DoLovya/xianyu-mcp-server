## 1. MCP Tool 接口层更新（server.py）

- [x] 1.1 在 `list_conversations` 装饰器函数签名中增加 `only_top: bool = False` 参数
- [x] 1.2 更新 docstring，说明 `only_top` 参数含义及与 `include_hidden`、`max_items` 的组合关系
- [x] 1.3 将 `only_top` 参数透传给 `_get_tools().list_conversations(...)` 调用

## 2. 业务逻辑层更新（xianyu_api_tools.py）

- [x] 2.1 在 `XianYuApiTools.list_conversations` 方法签名中增加 `only_top: bool = False` 参数
- [x] 2.2 保留现有 `summaries` 归一化步骤，在 `include_hidden` 过滤之后追加 `only_top` 过滤逻辑（若 `only_top=True`，仅保留 `summary.get("is_top") == True` 的条目）
- [x] 2.3 计算并写入返回 JSON 的 `top_count` 字段：
  - 当 `only_top=False` 时：`top_count` 为可见性过滤后的 `summaries` 中 `is_top=True` 的条数
  - 当 `only_top=True` 时：`top_count` 等于最终 `count`
- [x] 2.4 确保 `max_items` 截断发生在所有过滤之后，保持原有 `modify_time` 排序

## 3. 验证与测试

- [x] 3.1 对 `server.py` 和 `xianyu_api_tools.py` 运行项目 lint/typecheck（如有），确保无语法/类型错误
- [x] 3.2 手工冒烟验证（可选，需登录态）：调用 `list_conversations(only_top=True)` 确认仅返回 `is_top=true` 的会话，且 `top_count` 与 `count` 一致
- [x] 3.3 调用默认参数 `list_conversations()`（不传 `only_top`）确认行为与旧版本一致，`top_count` 正确反映置顶总数
