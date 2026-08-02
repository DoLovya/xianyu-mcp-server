## Context

`xianyu-mcp-server` 当前以 `.env` 中的 `XIANYU_COOKIE` 作为唯一登录态输入。Cookie 失效/风控后需要人工重新抓取，并且“扫码登录”尚未 MCP 化（README 已明确列为未支持能力）。

现有仓库内已包含一份对 `zhinianboke/xianyu-auto-reply` 的扫码登录逆向分析文档（`xianyu-qr-login-analysis/`），以及底层 `third_party/pyxianyu` 提供的 mtop 签名实现（`_m_h5_tk` token + MD5 sign），可复用其签名常量与 Cookie 解析逻辑。

## Goals / Non-Goals

**Goals:**
- 在 MCP 进程内实现“纯 HTTP”的闲鱼扫码登录（不启动浏览器），并对外暴露 3 个 MCP 工具：生成二维码 / 查询状态 / 获取 Cookie。
- 支持扫码确认后触发的风控分支：输出人脸验证二维码，并在用户完成验证后收集 Cookie。
- 会话仅驻留内存，自动过期回收；响应与日志不泄露完整 Cookie。

**Non-Goals:**
- 不实现自动写入 `.env` 或任何持久化账号库（避免误落盘与账号管理范畴膨胀）。
- 不实现“常驻监听消息”或 WebSocket 长连生命周期管理（该能力由其他模块/进程承担）。
- 不承诺对闲鱼页面结构变更的长期兼容（该链路依赖 HTML 正则提取，天然脆弱）。

## Decisions

- **接口链路选择（逆向 H5 登录页）**：沿用 `passport.goofish.com` 的 H5 扫码链路（`mini_login.htm` → `qrcode/generate.do` → `qrcode/query.do`），与参考实现一致，避免引入浏览器自动化。
- **异步 HTTP 客户端**：引入 `httpx.AsyncClient`，在单一 client 内贯穿多次跳转/轮询，保持 cookie jar 连续性。
- **二维码渲染**：引入 `qrcode`（PIL 后端），统一输出 `data:image/png;base64,...`，便于 MCP 客户端直接展示。
- **会话存储**：在进程内维护 `sessions: dict[str, Session]`，以 `session_id` 作为查询键；通过 `asyncio.create_task` 启动后台轮询；过期/终态自动清理。
- **安全策略**：所有日志与错误信息只允许输出“预览/摘要”（例如 cookie 数量、关键字段是否存在），严禁输出完整 Cookie；Cookie 仅在 `qr_login_cookie` 工具中显式返回。

## Risks / Trade-offs

- **[接口/页面结构变更]** → 提取 `window.viewData`、`htoken`、`verify_modes`、`Qrcode(text=...)` 均依赖正则；通过集中封装“解析函数 + 单元测试样本”降低回归成本。
- **[触发风控/滑块]** → 该链路仍可能触发 `FAIL_SYS_USER_VALIDATE` 或更强校验；通过降低轮询频率、增加抖动、控制并发会话数量来缓解。
- **[MCP 客户端展示能力差异]** → 并非所有客户端都能直接渲染 data-url；仍保留 `qr_content`（原始 URL）作为备选输出（实现上可选）。

## Migration Plan

- 仅新增 MCP 工具与依赖，现有工具保持兼容。
- 发布后用户可以选择继续使用“手动 Cookie”，或改用扫码登录获取新 Cookie 并手动写入 `.env`（推荐做法，避免自动落盘）。

## Open Questions

- MCP 工具命名是否保持与参考实现一致（`qr_login_generate/status/cookie`），还是需要更贴合现有命名风格（例如 `generate_qr_login`）？
- 是否需要提供 `qr_login_cancel(session_id)` 显式取消接口，用于快速释放会话资源？
