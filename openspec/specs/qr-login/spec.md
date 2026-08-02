# qr-login Specification

## Purpose
TBD - created by syncing change qr-login. Update Purpose after sync.
## Requirements

### Requirement: MCP 工具提供扫码登录能力
系统 MUST 通过 MCP 工具对外提供“生成二维码 / 查询状态 / 获取 Cookie”的扫码登录能力，且不依赖浏览器自动化。

#### Scenario: 生成二维码会话
- **WHEN** 调用方执行 `qr_login_generate`
- **THEN** 系统返回 `session_id` 与二维码图片 `qr_data_url`（`data:image/png;base64,...`）

#### Scenario: 查询扫码状态
- **WHEN** 调用方执行 `qr_login_status(session_id)`
- **THEN** 系统返回该会话的 `status`，其取值 MUST 属于 `waiting | scanned | verification_required | success | expired | cancelled | error`

#### Scenario: 获取 Cookie
- **WHEN** 调用方执行 `qr_login_cookie(session_id)`
- **THEN** 若会话 `status=success`，系统返回完整登录 Cookie 字符串；否则 MUST 拒绝返回 Cookie，并给出失败原因

### Requirement: 会话内存管理与超时回收
系统 MUST 在 MCP 进程内维护扫码登录会话（内存态），并在超时后自动失效，避免无限增长。

#### Scenario: 会话默认 5 分钟过期
- **WHEN** 会话创建超过默认有效期（5 分钟）
- **THEN** 系统将其标记为 `expired` 且后续不再继续轮询

#### Scenario: 人脸验证触发时延长会话窗口
- **WHEN** 系统检测到扫码确认后触发风控（`iframeRedirect=true`）
- **THEN** 系统将会话置为 `verification_required`，并延长会话有效期窗口以允许用户完成刷脸

### Requirement: 风控人脸验证分支可用
当扫码确认触发人脸验证时，系统 MUST 输出人脸验证二维码，并在用户完成刷脸后收集登录 Cookie。

#### Scenario: 产生人脸验证二维码
- **WHEN** 会话进入 `verification_required`
- **THEN** 系统返回 `face_qr_data_url` 供调用方展示给用户扫码

#### Scenario: 刷脸完成后成功落 Cookie
- **WHEN** 用户在手机端完成刷脸验证
- **THEN** 系统将会话置为 `success`，并可通过 `qr_login_cookie` 获取 Cookie

### Requirement: 安全与隐私
系统 MUST 避免在日志或异常堆栈中输出完整 Cookie；Cookie MUST 不自动写入 `.env` 或磁盘文件。

#### Scenario: 成功响应中不包含日志泄露
- **WHEN** 任意扫码登录工具返回成功或失败响应
- **THEN** 响应内容与日志中 MUST NOT 出现完整 Cookie（除 `qr_login_cookie` 工具的明确返回值）
