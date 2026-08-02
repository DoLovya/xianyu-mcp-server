## ADDED Requirements

### Requirement: QR login session status MUST advance reliably
系统 MUST 在二维码登录会话创建后，持续推进会话状态，并在调用方查询状态时反映真实进度，而不是长期停留在 `waiting` 直到过期。

#### Scenario: Session advances from waiting to scanned
- **WHEN** 用户在闲鱼 App 扫描二维码但尚未确认登录
- **THEN** 会话状态 MUST 从 `waiting` 变更为 `scanned`

#### Scenario: Session advances to verification_required
- **WHEN** 扫码确认触发风控或需要验证
- **THEN** 会话状态 MUST 变更为 `verification_required`
- **THEN** 状态数据 MUST 包含 `verification_url` 或可用于继续验证的信息

#### Scenario: Session advances to success
- **WHEN** 用户扫码并确认登录，且后续 cookie 补齐完成
- **THEN** 会话状态 MUST 变更为 `success`

### Requirement: Monitoring MUST work when generate is executed via asyncio.run
当会话创建发生在短生命周期事件循环（例如 `asyncio.run()`）中时，状态推进机制 MUST 不依赖该事件循环的存活。

#### Scenario: First-run setup triggers generate via asyncio.run
- **WHEN** first_run_setup 通过 `asyncio.run()` 执行二维码会话创建并返回给同步轮询逻辑
- **THEN** 会话状态推进 MUST 仍然有效（可从 `waiting` 进入其它状态或自然过期）

### Requirement: m_h5_tk preheat MUST be retried and SHOULD not warn by default
在二维码生成前的 m_h5_tk 预热尝试 MUST 进行有限重试，并在失败时允许降级继续；默认日志级别下 SHOULD 不产生高频 warning（避免误导与噪音）。

#### Scenario: Preheat retries then degrades
- **WHEN** m_h5_tk 预热第一次请求未获取到 token
- **THEN** 系统 MUST 进行有限次数重试（例如 2~3 次）
- **THEN** 若仍失败，系统 MUST 降级继续生成二维码（不因该步骤失败而阻断）

