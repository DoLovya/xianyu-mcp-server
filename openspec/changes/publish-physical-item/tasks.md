# Tasks

* [x] Task 1: 在 `core/client.py` 中新增 `item_publish_url`（`mtop.idle.pc.idleitem.publish/1.0/`）

* [x] Task 2: 在 `apis/item_api.py` 中新增 `publish_item(payload)` 方法，调用 publish 端点

* [x] Task 3: 在 `goofish_apis.py` 中暴露 `publish_item` 入口

* [x] Task 4: 在 `XianYuApiTools` 中新增 `publish_physical_item` 方法

  * 参数：`title`、`price`、`desc`、`images`（图片路径列表，至少 1 张）

  * 内部：上传图片 → 构造 payload → 调用 publish

  * 构造 payload 时使用合理默认值（分类、运费等）

* [x] Task 5: 在 `server.py` 中注册 `publish_physical_item` 工具

* [ ] Task 6: **实际发布一件实体商品**

  * 收集用户提供的商品信息（标题、价格、描述、图片）

  * 调用 MCP 工具发布

  * 确认发布成功，记录新商品 ID

