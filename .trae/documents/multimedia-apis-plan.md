## Summary

补齐/梳理 xianyu-mcp-server 的“多媒体（图片/视频/音频）”能力边界，并新增一个通用的 `upload_media` MCP 工具，用于显式上传本地文件或 URL 资源，返回可复用的 goofish 资源 URL（以及可选的像素信息）。

## Current State Analysis

### 现有多媒体相关能力（已存在）

- **图片上传（内部能力，未暴露为独立工具）**
  - 底层：`third_party/pyxianyu/apis/media_api.py` 的 `MediaApi.upload_media(media_path)` 会将本地文件上传到 `stream-upload.goofish.com/api/upload.api`。
  - 目前 MIME 仅覆盖：jpg/jpeg/png/webp（其余扩展名默认 image/png）。
- **发图片消息（已暴露工具）**
  - MCP 工具：`send_image_message(to_user_id, item_id, image)`
  - 实现：`src/xianyu_mcp/tools/xianyu_api_tools.py` 中会先上传图片，再通过 `make_image(url,width,height)` 发送。
  - `image` 已支持本地绝对路径或 http/https URL（URL 会先下载到临时文件）。
- **发布商品图（已暴露工具）**
  - MCP 工具：`publish_physical_item(title, price, desc, images)`
  - 实现：会对 `images` 逐张上传，再写入 `imageInfoDOList`。
  - 本次已改造为：基于 `preget()` 的模板构造 payload，避免“简化 payload”导致的 `FAIL_BIZ_IDLE_UNKNOWN_THROWABLE`。
- **二维码（data-url）**
  - `qr_login_generate` 返回二维码 data-url，本质也是一种“图像输出”，但不涉及上传。

### 现状缺口

- **缺少独立的“上传媒体”工具**：目前上传只隐藏在 `send_image_message` / `publish_physical_item` 内，外部无法复用上传结果（例如：先上传 -> 再批量构造 payload -> 再 edit/publish）。
- **视频/音频不可用/不明确**：
  - `pyxianyu.message` 已有 `make_audio`，但 MCP 侧未提供 `send_audio_message`。
  - `MediaApi.upload_media` 的 MIME 映射未覆盖 mp4/mov/mp3 等，且是否可用于视频/音频上传需要验证。

## Proposed Changes

### 1) 新增 MCP 工具：upload_media

- **文件**：`src/xianyu_mcp/server.py`
- **新增接口**：`@mcp.tool() def upload_media(media: str) -> str`
  - 入参 `media`：本地绝对路径或 http/https URL（与 `send_image_message` 入参风格一致）。
  - 输出（JSON 字符串）建议结构：
    - `success: bool`
    - `url: str`（上传后资源 URL，供后续 make_image / 商品 payload 复用）
    - `pix: str`（若接口返回，例如 "1440x1920"）
    - `width/height: int`（若可解析 pix）
    - `raw: dict`（原始 upload 返回，方便调试）
- **鉴权/首次配置**：沿用 `_maybe_requires_login_payload()`，缺 Cookie 时直接返回首次配置引导 payload。
- **护栏**：作为写操作走 `RequestGuardrails.run_write_steps`（与其他写操作一致，确保全局串行化与风控策略生效）。

### 2) 新增工具实现：XianYuApiTools.upload_media

- **文件**：`src/xianyu_mcp/tools/xianyu_api_tools.py`
- **新增方法**：`def upload_media(self, media: str) -> str`
  - 复用现有 `_prepare_image` 的“URL 下载到临时文件 + 自动清理”逻辑（建议将其更名为更通用的 `_prepare_media`，或保留命名但扩大语义；本计划先保守：新增 `_prepare_media`，内部调用/复用现有逻辑，避免语义漂移）。
  - 上传：`self._get_media_api().upload_media(local_path)`
  - 解析：从返回的 `object.url` 与 `object.pix` 产出 `url/width/height`（pix 不存在时保持 0）。
  - 清理：若是从 URL 下载的临时文件，finally 中删除临时文件（与 `send_image_message` 现有模式一致）。

### 3) 扩展底层 MIME 映射（为“图片+视频（若可行）”做准备）

- **文件**：`third_party/pyxianyu/apis/media_api.py`
- **改动点**：扩充 `mime` 映射与默认值：
  - 图片：jpg/jpeg/png/webp（保持）
  - 视频（候选）：mp4 -> video/mp4，mov -> video/quicktime，mkv -> video/x-matroska（若需要）
  - 音频（候选）：mp3 -> audio/mpeg，m4a -> audio/mp4，wav -> audio/wav，aac -> audio/aac，amr -> audio/amr
  - 默认：`application/octet-stream`（比默认 image/png 更合理）
- **注意**：此步骤只解决“客户端声明 MIME”问题，不保证闲鱼端接受对应类型；需要通过验证步骤确认。

### 4) 文档补齐

- **文件**：`README.md`（以及如有：`docs/*`）
- 增加 `upload_media` 的用法示例与典型工作流：
  - 上传图片 -> 拿到 url -> 用于 `edit_item`（overrides/payload）或自定义 payload
  - 上传图片 -> 直接传给 `send_image_message` / `publish_physical_item`（对比：两种方式都可用）

## Assumptions & Decisions

- `upload_media` 定位为“通用上传”，并不直接发送消息/发布商品，仅返回可复用 URL。
- 多媒体范围以“图片”为必达；视频/音频作为“尽力支持”，通过 MIME 扩展 + 实测决定可用性。
- 所有上传相关调用都必须走写护栏（全局串行 + 风控）。

## Verification

- 启动 MCP（stdio 或 http 均可），调用：
  - `upload_media`（本地 jpg/png/webp）
  - `upload_media`（http/https 图片 URL）
  - 若要验证视频：准备一个小体积 mp4，调用 `upload_media`，确认是否返回 `success` 与 `object.url`（失败则记录 ret/错误码并回退为“不支持视频”）。
- 回归验证：
  - `send_image_message` 仍可正常使用 URL 图片（确保临时下载逻辑不回退）
  - `publish_physical_item` 仍可正常发布（至少一张图）

