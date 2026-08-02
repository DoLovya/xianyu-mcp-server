## Context

- 上传能力来源于 `third_party/pyxianyu/apis/media_api.py` 的 `MediaApi.upload_media(media_path)`，其输入为本地文件路径。
- 现有 MCP 已支持 `send_image_message` 与 `publish_physical_item`，但上传逻辑对外不可复用；且 URL 资源需要先下载到本地临时文件才能上传。
- 所有写操作需要通过 `RequestGuardrails` 串行化与限速，避免触发风控。
- 视频/音频是否被闲鱼 PC 上传端点接受不确定，需要通过扩展 MIME + 实测来确认能力边界。

## Goals / Non-Goals

**Goals:**

- 新增 `upload_media(media)` MCP 工具，用于显式上传素材并返回可复用 URL。
- 复用统一的“URL 下载 + 临时文件清理 + 上传”流程，减少重复实现。
- 扩展 MIME 映射，为视频/音频提供合理的 Content-Type（能力可行则启用，不可行则以错误返回体现）。

**Non-Goals:**

- 不实现商品视频位/视频封面等复杂发布能力。
- 不实现会话语音消息发送工具（可在后续变更集中引入）。
- 不引入并发上传；所有上传仍按护栏的写序列化策略执行。

## Decisions

- 决策 1：将 `upload_media` 作为独立 MCP 工具暴露，返回上传结果（url/pix/width/height/raw），上层流程（发布/编辑/发消息）可选择复用该工具输出。
- 决策 2：将 URL 素材下载行为内聚到工具层（`XianYuApiTools`），并使用临时文件 + finally 删除，避免仓库污染与资源泄漏。
- 决策 3：扩展 `MediaApi.upload_media` 的 MIME 映射并将默认值调整为 `application/octet-stream`，为非图片类型提供更合理的默认声明。

## Risks / Trade-offs

- 风控冷却触发频率增加 → 通过 `RequestGuardrails` 的写限速与串行化控制，并在文档中提示用户预期。
- 视频/音频上传被服务端拒绝 → `upload_media` 返回原始错误信息；文档明确“尽力支持”，以实测结果为准。
- URL 下载可能被 CDN 拦截 → 复用现有下载请求头（referer/user-agent/accept），必要时进一步增强。
