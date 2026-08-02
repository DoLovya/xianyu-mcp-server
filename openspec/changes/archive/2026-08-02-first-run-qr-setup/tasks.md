## 1. Setup Orchestrator

- [x] 1.1 新增首次配置状态管理模块（current_session_id/local_url/qr_data_url/状态机）
- [x] 1.2 实现后台 orchestrator：缺 Cookie 时自动 `qr_login_generate`、轮询状态、成功后写入 `.env`
- [x] 1.3 增加环境变量开关（禁用自动 setup / 禁用自动打开浏览器 / 禁用自动写入 .env）

## 2. Local Web UI

- [x] 2.1 增加本机 HTTP 页面（绑定 127.0.0.1 + 随机端口）展示二维码与状态
- [x] 2.2 增加 `/status` JSON 接口并在页面上自动轮询刷新
- [x] 2.3 verification_required 时在页面展示 verification_url/人脸二维码

## 3. MCP Tool Gating

- [x] 3.1 在 server.py 增加未登录拦截：非 `qr_login_*`/setup 工具统一返回 requires_login JSON
- [x] 3.2 在拦截响应中包含 session_id/local_url/qr_data_url/status
- [x] 3.3 确保不在日志中输出 Cookie 明文

## 4. Docs & Tests

- [x] 4.1 README 增加“首次配置模式”说明与开关说明
- [x] 4.2 新增单测覆盖状态机与 requires_login 响应（mock 掉网络/浏览器打开）
