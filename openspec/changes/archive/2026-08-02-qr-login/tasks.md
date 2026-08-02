## 1. 依赖与结构

- [x] 1.1 在 `pyproject.toml` 增加扫码登录所需依赖（`httpx`、`qrcode[pil]`）
- [x] 1.2 新增扫码登录模块目录（`src/xianyu_mcp/qr_login/`），规划会话模型与对外 API

## 2. 核心实现（二维码链路）

- [x] 2.1 实现会话模型（状态机、过期判断、cookie jar、输出字段）
- [x] 2.2 实现“生成二维码”流程：获取 `_m_h5_tk` → 抓取 `mini_login.htm` → 调用 `generate.do` → 渲染 `qr_data_url`
- [x] 2.3 实现后台轮询：`query.do` 轮询更新状态（`waiting/scanned/success/expired/cancelled`）

## 3. 风控分支（人脸验证）

- [x] 3.1 实现 `iframeRedirect=true` 分支识别与会话字段回填（`verification_required`、`verification_url`）
- [x] 3.2 实现人脸验证链路：跟随跳转提取 `htoken`、解析并渲染 `face_qr_data_url`、轮询 `check.do`、跟随 `ivCheckLogin` 收集 Cookie

## 4. MCP 接入

- [x] 4.1 在 `src/xianyu_mcp/server.py` 注册 MCP 工具：`qr_login_generate`、`qr_login_status`、`qr_login_cookie`
- [x] 4.2 为工具输出定义稳定 JSON 结构（`session_id/status/qr_data_url/face_qr_data_url/cookies` 等），并确保不在日志中泄露 Cookie

## 5. 测试与文档

- [x] 5.1 使用 `unittest` 增加解析函数与状态流转的单元测试（不依赖真实网络）
- [x] 5.2 更新 `README.md`：补充扫码登录工具说明与安全注意事项
