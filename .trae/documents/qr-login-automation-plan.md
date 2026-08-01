# 二维码登录免浏览器 Cookie 方案（计划）

## Summary
目标：把现有 `qr_login_*` 扫码链路升级为“扫码后即可直接用于 MCP 读写 API”的 Cookie 获取流程，最大化自动化，尽量减少用户从浏览器复制 Cookie 的操作。

成功标准：
- 用户仅通过 `qr_login_generate → 扫码确认 → qr_login_cookie` 即可得到包含 `_m_h5_tk/_m_h5_tk_enc` 的 Cookie，随后 `validate_login` 能拿到 `accessToken`。
- 在触发风控/验证时，工具能返回（并在 CLI 中自动打开）验证链接/人脸二维码，用户完成一次验证后可继续自动补齐 Cookie。
- 不在日志中泄露完整 Cookie；仅在 `qr_login_cookie` / 显式的“写入 .env”工具中返回或落盘。

## Current State Analysis
代码现状（基于仓库当前实现）：
- `qr_login_generate/status/cookie` 通过 `passport.goofish.com` 链路生成二维码、轮询确认、收集会话 cookies（见 [manager.py](file:///Users/huan.zhang/Code/xianyu-mcp-server/src/xianyu_mcp/qr_login/manager.py)）。
- 这条链路常见只拿到 `cookie2/unb/t/...` 等“登录态”Cookie，但不保证拿到 mtop 签名必须的 `_m_h5_tk/_m_h5_tk_enc`。
- MCP 大部分业务接口依赖 mtop 签名，`third_party/pyxianyu` 在缺 `_m_h5_tk` 时直接报错（见 [client.py](file:///Users/huan.zhang/Code/xianyu-mcp-server/third_party/pyxianyu/core/client.py#L100-L105)），从而导致你必须去浏览器复制更“全”的 Cookie。
- 当前仓库内已有风控分支（人脸 iframeRedirect → `verification_required`）与 CLI 自动打开二维码图片的能力，但缺少“扫码成功后自动补齐 mtop Cookie”的闭环。

关键结论：
- “扫码登录成功” ≠ “具备 mtop 签名 token（`_m_h5_tk`）”。
- `_m_h5_tk` 往往由 `h5api.m.goofish.com` 域的特定 mtop 接口下发；需要在扫码成功后额外触发一次“发 tk”的请求并合并 Set-Cookie。
- `x5sec` 属于更强风控 cookie：可尝试自动获取/刷新，但在部分账号/时段可能需要人工完成一次验证码/校验，无法保证 100% 无交互。

## Proposed Changes

### 1) 扫码成功后自动补齐 mtop Cookie（核心）
文件：`src/xianyu_mcp/qr_login/manager.py`

新增一个“成功后补齐”步骤，在会话进入 `success`（或刷脸成功）后执行：
- 新增 `_bootstrap_mtop_cookies(session)`：
  - 输入：当前会话 cookies（至少包含 `cookie2`）。
  - 行为：调用 `https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/`（无需签名的引导接口）来触发服务端下发 `_m_h5_tk/_m_h5_tk_enc`（以及可能的 `x5sec*`）。
  - 关键点：请求 cookies 仅携带 `cookie2`（实践中更容易下发 tk，且减少风控特征），其余 cookie 由服务端下发后再合并到会话 cookies。
  - 结果写回：把 response cookies 合并进 `session.cookies`，并在 `to_public_dict()` 里可选附带 `has_mtop_token` / `has_x5sec` 等布尔标记（不包含敏感明文）。
- 若拿到 `_m_h5_tk/_m_h5_tk_enc`：保持 `success`，`qr_login_cookie` 返回的 cookie 直接可用于 `validate_login/list_my_items/...`。
- 若只拿到 `x5secdata/x5sectag` 或接口返回强风控信号：
  - 会话置为 `verification_required`（或沿用现有 `verification_required`），并尽可能提供 `verification_url`（若响应体/跳转中携带可打开的验证链接；否则提供“需要浏览器/手机端验证”的提示文案）。
  - 延长 `expire_time`，允许用户完成验证后继续轮询/重试 bootstrap。
- 在轮询任务中，遇到 `verification_required` 后增加“周期性重试 bootstrap”的逻辑（例如每隔 N 秒重试一次，直到成功或过期），使用户验证完成后能自动转为 `success`。

### 2) 会话过期策略与规范对齐
文件：`src/xianyu_mcp/qr_login/models.py`

根据现有规格（见 [qr-login/spec.md](file:///Users/huan.zhang/Code/xianyu-mcp-server/openspec/changes/qr-login/specs/qr-login/spec.md#L21-L28)）：
- 默认会话有效期恢复为 300s（5 分钟）。
- 当进入 `verification_required`（刷脸/风控验证）时，将该会话有效期延长到 900s（或更长但有上限），避免用户来不及完成验证。

### 3) 增加“显式写入 .env”的工具（可选，但符合你“尽量全自动”的目标）
文件：`src/xianyu_mcp/server.py`

新增 MCP 工具（写操作、需显式调用）：
- `qr_login_save_env(session_id: str, env_path: str = ".env")`
  - 前置：会话 `status == success` 且 cookie 中已包含 `_m_h5_tk`（否则拒绝并提示原因）。
  - 行为：将 `XIANYU_COOKIE="..."` 写入指定 env 文件（默认仓库根 `.env`），并确保只改动这一项。
  - 安全：不在日志打印 Cookie，只在返回值中给出 `success/updated_path/has_m_h5_tk/has_x5sec` 等信息。

说明：
- 这不违反“Cookie 不自动写入磁盘”的安全要求，因为它是用户显式调用的工具（而不是扫码成功后自动落盘）。

### 4) CLI 体验：自动打开二维码/验证页面，减少人工步骤
文件：`scripts/qr_login_cli.py`

增强 CLI 行为（不影响 MCP 工具的纯度）：
- 扫码二维码：已支持自动打开 `/tmp/*.png`，保留。
- 进入 `verification_required` 时：
  - 若有 `verification_url`：`open <url>` 自动打开验证页面。
  - 若有 `face_qr_data_url`：保存为 PNG 并自动打开。
- 当检测到 `success` 且已补齐 `_m_h5_tk`：打印“可直接用于 MCP”的提示，并可选提示用户调用 `qr_login_save_env`（或 CLI 内直接调用写入逻辑，按你的偏好二选一）。

### 5) 文档与故障指引更新
文件：`README.md`

更新“常见问题”与推荐流程：
- 强调：扫码 cookie 经过“补齐步骤”后可直接用；不再默认要求浏览器复制。
- 说明限制：若触发 `FAIL_SYS_USER_VALIDATE` 或强风控，仍可能需要用户完成一次验证；工具会提供链接并自动打开（CLI）。

### 6) 测试策略（防回归）
文件：`tests/`（新增或扩展）

建议新增单测覆盖：
- `QRLoginManager` 在不同响应下对 `qrCodeStatus` / `verification_required` / `success` 的状态流转。
- `_bootstrap_mtop_cookies` 合并 cookies 的行为（使用 httpx mock / responses mock），确保不会把 cookie 明文写日志。

## Assumptions & Decisions
- 无法承诺 100% “零交互拿到 x5sec”：x5sec 本质上是风控产物，部分场景需要人工验证（滑块/验证码/刷脸）。方案目标是：**自动检测 + 自动打开验证入口 + 验证后自动续航**。
- MCP 层保持“默认无副作用”：`qr_login_generate/status/cookie` 不写文件；只有显式 `qr_login_save_env` 才会写 `.env`。
- 写操作全局串行、读写限速继续由 `guardrails.py` 负责；二维码登录属于认证流程，不纳入业务写操作并发约束。

## Verification Steps
1. 启动 MCP（stdio 或 http 均可）。
2. 调用 `qr_login_generate`，展示二维码并扫码确认。
3. 轮询 `qr_login_status`：
   - 若 `verification_required`：确认 CLI 自动打开验证页面/人脸二维码；完成验证后状态应转为 `success`。
4. 调用 `qr_login_cookie`：
   - 断言 cookie 中包含 `_m_h5_tk` / `_m_h5_tk_enc`。
5. 直接调用 `validate_login`：
   - 断言 `success=true` 且拿到 `accessToken`。
6. 调用 `list_my_items` / `list_conversations` 做端到端冒烟测试。
7. （可选）调用 `qr_login_save_env`，重启/重载 MCP 后再次调用 `validate_login` 确认 `.env` 生效。

