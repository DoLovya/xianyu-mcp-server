# first-run-qr-setup Specification

## Purpose
当闲鱼 MCP 缺少可用 Cookie 时，系统应提供“首次配置”体验：自动生成扫码二维码并展示在本机网页中，引导用户完成登录，并在成功后自动写入 `.env`，使后续工具可直接使用。

## Requirements

### Requirement: 缺 Cookie 时自动进入首次配置模式
系统 SHALL 在启动时检测 `XIANYU_COOKIE` 与 `XIANYU_COOKIE_FILE`。

#### Scenario: 未配置 Cookie — 自动开始扫码引导
- **GIVEN** `XIANYU_COOKIE` 为空且未配置 `XIANYU_COOKIE_FILE`
- **WHEN** MCP 服务启动
- **THEN** 系统 SHALL 自动创建二维码登录会话并生成 `session_id`
- **THEN** 系统 SHALL 启动仅绑定 `127.0.0.1` 的本机网页用于展示二维码
- **THEN** 系统 SHOULD 尝试自动打开默认浏览器到该网页

### Requirement: 未登录状态下的工具调用必须可被结构化引导
当 Cookie 缺失或不可用时，除 `qr_login_*`/setup 工具外，其它工具调用 SHALL 返回结构化 JSON，引导用户完成登录。

#### Scenario: 调用任意业务工具 — 返回 requires_login
- **GIVEN** 当前未完成首次配置（未持有可用 Cookie）
- **WHEN** 客户端调用任意非 `qr_login_*`/setup 工具
- **THEN** 系统 SHALL 返回包含以下字段的 JSON：
  - `success=false`
  - `requires_login=true`
  - `session_id`
  - `status`（`waiting/scanned/verification_required/expired/error`）
  - `local_url`（本机网页地址）
  - `qr_data_url`（data-url 兜底）

### Requirement: 扫码成功后自动补齐 mtop Token 并写入 .env
系统 SHALL 在会话登录成功后自动补齐 mtop Token，并将 Cookie 写入 `.env`，使后续工具可直接使用。

#### Scenario: 扫码确认 — 自动补齐并落盘
- **GIVEN** 二维码会话状态进入 `success`
- **WHEN** 系统获取会话 Cookie
- **THEN** 系统 SHALL 确保 Cookie 中包含 `_m_h5_tk` 与 `_m_h5_tk_enc`（必要时通过引导接口补齐）
- **THEN** 系统 SHALL 自动将 Cookie 写入仓库根目录 `.env` 的 `XIANYU_COOKIE`
- **THEN** 系统 SHALL 使后续 `validate_login` 等工具可直接成功调用

### Requirement: 风控/验证流程可续航
系统 SHALL 在触发风控或验证时提供可继续验证的入口信息，并持续推进会话直至成功或过期。

#### Scenario: 触发验证 — 自动展示验证入口并持续重试
- **GIVEN** 会话状态进入 `verification_required`
- **WHEN** 系统获得 `verification_url` 或 `face_qr_data_url`
- **THEN** 系统 SHALL 在本机网页中展示验证入口信息
- **THEN** 系统 SHOULD 在 CLI 环境自动打开验证入口（若可用）
- **THEN** 用户完成验证后，系统 SHALL 持续重试直至进入 `success` 或过期
