## Why

当前项目必须依赖“浏览器抓 Cookie + 手动写入 `.env`”才能使用 MCP 工具；一旦 Cookie 失效或触发风控，恢复成本高、流程不可自动化。引入“纯 API 的扫码登录”可以把登录态获取流程 MCP 化，降低接入门槛并提升可维护性。

## What Changes

- 新增一组“扫码登录”MCP 工具：生成二维码、查询状态、获取登录 Cookie。
- 在 MCP 进程内实现会话管理与后台轮询任务（内存态、超时自动回收）。
- 支持风控分支：当扫码确认后触发 `iframeRedirect` 时，进入人脸验证链路并输出人脸二维码。
- 增加实现所需的第三方依赖（HTTP 异步客户端、二维码渲染）。
- 更新文档：补充扫码登录使用方法与安全注意事项（Cookie 不落盘、不在日志中输出）。

## Capabilities

### New Capabilities

- `qr-login`: 在不启动浏览器的前提下，通过逆向 `passport.goofish.com` 的接口实现闲鱼扫码登录（含人脸验证分支），并以 MCP 工具对外提供“生成二维码 / 查询状态 / 获取 Cookie”能力。

### Modified Capabilities

- （无）

## Impact

- 代码影响：`src/xianyu_mcp/server.py`（新增 MCP 工具注册）、新增扫码登录模块目录（会话管理、轮询、人脸验证）。
- 依赖影响：新增 `httpx`、`qrcode`（含 PIL 后端）。
- 外部系统：调用 `passport.goofish.com` 与相关风控验证页面；该链路对闲鱼页面结构变化较敏感。
