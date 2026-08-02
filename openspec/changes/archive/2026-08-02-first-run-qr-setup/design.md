## Context

现有服务启动后会读取仓库根目录 `.env` 的 `XIANYU_COOKIE` / `XIANYU_COOKIE_FILE`（见 `src/xianyu_mcp/server.py`）。当 Cookie 缺失时，多数工具会在内部抛错或由下游 mtop/签名流程报错；同时，二维码登录链路虽然存在，但需要用户手动调用工具并复制 Cookie 落盘，缺少“首次配置”体验。

约束：
- MCP 服务通常在本机运行，但也可能被远程/无 GUI 环境启动；因此“弹窗/自动打开网页”必须可禁用且有输出兜底
- Cookie 属于敏感信息：禁止写入日志；自动写入 `.env` 必须确保仓库默认不会提交该文件
- 风控场景不可完全消除：目标是“自动检测 + 自动展示验证入口 + 验证后自动续航”

## Goals / Non-Goals

**Goals:**
- 缺 Cookie 时自动进入首次配置流程：生成二维码并在本机打开网页展示
- 扫码成功后自动补齐 `_m_h5_tk/_m_h5_tk_enc` 并写入 `.env`
- 未登录状态下的工具调用提供结构化引导响应（包含 `session_id`、`local_url`、`qr_data_url`、`status` 等）
- 风控/刷脸时自动展示验证入口（网页/CLI）

**Non-Goals:**
- 不追求 100% 无人工验证地获得 `x5sec`（取决于账号与风控）
- 不将 Cookie 同步到系统钥匙串/操作系统安全存储（仅 `.env`）
- 不修改 MCP 客户端（Cursor/Claude Desktop/Trae 等）的配置 UI 行为

## Decisions

### Decision 1: 用“限制工具 + 自动引导”模拟“必须配置”
选择：服务可正常启动，但在 Cookie 缺失时，除 `qr_login_*`/setup 工具外，其它工具返回统一的 `requires_login=true` JSON，而不是抛异常。

理由：MCP 协议没有统一的“配置向导”握手；通过工具层的结构化响应，可以在任意 MCP 客户端中实现一致的引导体验。

替代方案：无 Cookie 时直接退出进程。缺点：部分 MCP 客户端会把它当成“服务不可用”，体验更差。

### Decision 2: 本机网页展示二维码（127.0.0.1 + 随机端口）
选择：启动一个仅绑定 `127.0.0.1` 的轻量 HTTP 服务（标准库 `http.server`），提供：
- `/`：展示二维码与当前状态，带轮询刷新
- `/status`：返回 JSON（复用 `qr_login_status` 输出）

理由：比 data-url/PDF 更通用；也更符合“弹出网页”的直觉。

兜底：若无法打开浏览器或禁用自动打开，仍在 stderr/返回值里输出完整 `local_url` 和 `qr_data_url`。

### Decision 3: 自动写入 `.env` 的策略
选择：扫码成功后自动更新仓库根目录 `.env` 的 `XIANYU_COOKIE`。

理由：这是“首次配置完成即可长期可用”的关键；避免每次都复制 Cookie。

安全：不在日志中打印 Cookie 明文；仅写文件，并保持 `.env` 在 `.gitignore`。

### Decision 4: 通过后台任务实现“启动即弹出 + 不阻塞 MCP”
选择：当服务启动检测到 Cookie 缺失时，启动一个后台 setup orchestrator：
- 创建扫码会话
- 启动本机网页并尝试 `webbrowser.open(local_url)`
- 周期性轮询状态：`waiting/scanned/verification_required/success`
- 成功后写入 `.env` 并结束 setup；失败/过期则给出可重试提示

理由：不阻塞 `mcp.run()` 的主流程，同时满足“初次配置自动弹出”的诉求。

## Risks / Trade-offs

- [无 GUI / 远程运行无法自动打开网页] → 提供 env 开关禁用自动打开，并在 stderr/响应中输出 `local_url`/`qr_data_url`
- [Cookie 自动落盘可能被误提交] → README 强提醒；仓库约束要求 `.env` 不提交；CI 可追加检测（可选）
- [风控导致流程中断] → 统一进入 `verification_required`，在网页/CLI 中展示验证链接/二维码，并持续重试补齐

