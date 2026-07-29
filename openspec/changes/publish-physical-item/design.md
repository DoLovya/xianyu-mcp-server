## Context

闲鱼 PC 端"发布新商品"的 API 端点与"编辑已有商品"不同：
- 编辑：`mtop.idle.pc.idleitem.edit`（已有实现）
- 发布：`mtop.idle.pc.idleitem.publish`（需新增）

两个端点的 payload 结构高度相似，区别仅在于是否携带 `itemId`。

## Goals / Non-Goals

**Goals:**
- 实现 `mtop.idle.pc.idleitem.publish` API 调用
- 提供 `publish_physical_item` MCP 工具，接受商品标题、价格、描述、图片等基本信息
- 实际发布一件实体商品，为后续编辑测试提供测试数据

**Non-Goals:**
- 不处理复杂类目属性（特定类目下的额外字段）
- 不实现批量发布

## Decisions

**决策 1：复用 `edit_item` 的 payload 构造模式**
- `publish_item` 接收与 `edit_item` 类似的 payload 结构
- 不同点：不传 `itemId`，使用 `mtop.idle.pc.idleitem.publish` 端点
- 简化实现，降低重复代码

**决策 2：工具接口设计为"简化参数 → 构造 payload → 调用 publish"**
- 客户端只需要提供：标题、价格、描述、图片列表
- 其余字段（运费、分类等）使用合理默认值
- 图片先通过 `upload_media` 上传，将返回的 URL 填入 payload

## Risks / Trade-offs

- **publish 端点未实际验证**：需要发布时从抓包确认 payload 格式是否完全匹配
- **类目系统**：不同商品类目需要不同的 `itemCatDTO`，首次发布可能需要先用 web 端确认可用类目
