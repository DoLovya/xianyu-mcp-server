## Why

当前多媒体上传能力只隐藏在 `send_image_message` / `publish_physical_item` 内部，外部无法复用上传结果（例如：先上传素材，再在多个 API 中复用 URL 组装 payload）。同时，视频/音频的可行性不明确，需要补齐接口边界与可验证的能力面。

## What Changes

- 新增 MCP 工具 `upload_media(media)`：上传本地文件或 URL 资源，返回可复用的资源 URL 与可选的像素信息。
- 在服务端工具层新增 `XianYuApiTools.upload_media` 实现，复用现有“URL 下载到临时文件 + 自动清理 + 上传”的流程。
- 扩展底层上传的 MIME 映射，为视频/音频（若闲鱼侧允许）提供正确的 Content-Type。
- 补齐 README 文档，说明多媒体相关工具与典型工作流。

## Capabilities

### New Capabilities

- `media-upload`: 提供通用的媒体上传能力（图片必达；视频/音频尽力支持并可验证），以便在消息与商品等场景复用上传后的 URL。

### Modified Capabilities

无

## Impact

- 代码：`src/xianyu_mcp/server.py`、`src/xianyu_mcp/tools/xianyu_api_tools.py`、`third_party/pyxianyu/apis/media_api.py`、`README.md`
- 行为：新增一个写操作工具（需遵守全局串行与风控护栏），并可能引入对更多文件扩展名的上传支持。
