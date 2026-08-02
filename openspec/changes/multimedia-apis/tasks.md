## 1. Tool Surface

- [x] 1.1 Add MCP tool `upload_media(media: str)` in server.py
- [x] 1.2 Add `XianYuApiTools.upload_media(media: str)` implementation and wire it in server.py

## 2. Media Handling

- [x] 2.1 Add a shared prepare helper for URL download + temp file cleanup (reuse existing behavior)
- [x] 2.2 Extend MediaApi MIME mapping to cover common video/audio formats and use a safer default

## 3. Documentation

- [x] 3.1 Update README with upload_media usage and common workflows

## 4. Verification

- [x] 4.1 Manual verify upload_media with a local image and a remote image URL
- [x] 4.2 Manual verify (best-effort) video upload with a small mp4 and record result
