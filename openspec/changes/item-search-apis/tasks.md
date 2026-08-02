## 1. Evidence & Spec Baseline

- [x] 1.1 补全 `.trae/documents/闲鱼抓包报告_20260803.md` 的“商品搜索”部分（参数差异：默认/排序/翻页；响应字段要点）
- [x] 1.2 （可选）补充 `search.shade` 与 `item.search.activate` 的触发条件与字段结构（脱敏）

## 2. third_party API 封装

- [x] 2.1 在 `third_party/pyxianyu/core/client.py` 增加 `item_search_url` 常量（pc.search endpoint）
- [x] 2.2 新增 `third_party/pyxianyu/apis/search_api.py`，实现 `search_items`（调用 mtop.taobao.idlemtopsearch.pc.search）
- [x] 2.3 在 `third_party/pyxianyu/apis/__init__.py` 与 `goofish_apis.py` 暴露 SearchApi

## 3. MCP 工具封装

- [x] 3.1 在 `src/xianyu_mcp/tools/xianyu_api_tools.py` 增加 `search_items`（走 read guardrails）
- [x] 3.2 在 `src/xianyu_mcp/server.py` 暴露 MCP tool：`search_items`

## 4. 验证

- [x] 4.1 增加最小验证脚本或单元测试：校验请求 data 组装（keyword/page/sort）与缺少 `_m_h5_tk` 时的错误提示
- [x] 4.2 运行静态检查/测试（以仓库现有方式为准）
