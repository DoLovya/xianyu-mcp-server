## Why

当前闲鱼 MCP 依赖 `XIANYU_COOKIE` 才能调用 mtop API。对初次接入用户来说，从浏览器复制 Cookie 既繁琐又容易漏字段（`_m_h5_tk`/`x5sec`），导致“看似已登录但工具不可用”的体验落差。

希望把“登录/配置”变成 MCP 的首次必经流程：像 GitHub MCP 必须配置 Token 一样，闲鱼 MCP 在缺少 Cookie 时主动引导用户完成扫码登录，并在成功后自动写入 `.env`，做到一次配置长期可用。

## What Changes

- 启动时若未配置 `XIANYU_COOKIE`/`XIANYU_COOKIE_FILE`，服务自动进入“首次配置模式”，创建扫码会话并弹出本机网页展示二维码
- 缺少登录态时，除 `qr_login_*`/配置相关工具外，其它工具统一返回 `requires_login` 风格的结构化响应（而不是抛异常/下游报错）
- 扫码成功后自动补齐 mtop 关键字段（`_m_h5_tk/_m_h5_tk_enc`），并自动写入仓库根目录 `.env`
- 若触发风控（如需要验证/刷脸），网页/CLI 自动展示验证入口，用户完成后流程继续
- 全程避免在日志中输出完整 Cookie（仅写入 `.env` 或显式工具返回）

## Capabilities

### New Capabilities
- `first-run-qr-setup`: 缺 Cookie 时自动启动扫码配置（本机网页展示二维码、完成后自动写入 `.env`，并对未登录状态的工具调用返回结构化引导）

### Modified Capabilities
- (none)

## Impact

- 影响 MCP 服务启动逻辑与工具返回格式：需要在 `src/xianyu_mcp/server.py` 层增加“未登录拦截/引导”
- 新增本机网页展示二维码的轻量 Web 入口（仅绑定 `127.0.0.1`）
- 涉及敏感信息处理：Cookie 自动落盘到 `.env`，需保证不被提交（当前仓库已要求 `.env` 不提交）

