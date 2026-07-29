## Why

当前所有商品均为虚拟商品，`edit_item` 工具无法测试（编辑接口仅对实体商品有效）。需要新增发布实体商品的能力，先上架一件实体商品，再验证编辑链路。

## What Changes

- 在 `XianyuClient` 中新增 `item_publish_url` 端点
- 在 `ItemApi` 中新增 `publish_item(payload)` 方法，调用 `mtop.idle.pc.idleitem.publish`
- 在 `goofish_apis.py` 中暴露 `publish_item` 入口
- 在 `XianYuApiTools` 中新增 `publish_physical_item` MCP 工具
- 在 `server.py` 中注册该工具
- **实际执行**：实现后由我协助上传商品图片并发布一件实体商品

## Capabilities

### New Capabilities
- `item-publish`: 提供在闲鱼 PC 端发布全新商品的能力，支持设置标题、价格、描述、图片、分类、运费等

### Modified Capabilities
- 无

## Impact

- 新增依赖：需接入 `mtop.idle.pc.idleitem.publish` 端点
- 代码变更：`core/client.py`（新增 URL）、`apis/item_api.py`（新增 publish 方法）、`goofish_apis.py`、`xianyu_api_tools.py`、`server.py`
- 用户需提供商品图片（本地路径或 URL），由我协助完成发布操作
