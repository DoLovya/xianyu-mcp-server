## Why

当前二维码登录在“首次配置模式”(first_run_setup)下会出现长期停留在 `waiting`，最终 `expired` 的情况，导致用户扫码后看不到状态变化，也无法写入 `.env`。日志里还会频繁出现 “获取 m_h5_tk 失败，降级继续” 警告，增加排障成本。

## What Changes

- 使二维码登录状态推进在所有调用场景下都稳定可用（包括 first_run_setup 内部通过 `asyncio.run()` 触发的调用），确保 `waiting → scanned/verification_required/success` 能正确更新
- 对 m_h5_tk 预热获取增加重试与更稳健的 cookie 捕获策略，降低无意义告警频率（失败仍可降级继续）
- 补强关键可观测点：明确记录扫码阶段状态变化与进入风控/验证的原因，便于定位“为什么没成功/为什么过期”

## Capabilities

### New Capabilities

- `qr-login-monitoring`: 二维码登录会话的稳定状态推进与更可靠的 m_h5_tk 预热（覆盖 first_run_setup 场景）

### Modified Capabilities

- （空）

## Impact

- 影响模块：
  - `src/xianyu_mcp/qr_login/manager.py`（会话创建、状态轮询、mtop cookie 补齐）
  - `src/xianyu_mcp/qr_login/face_verification.py`（人脸验证后续 mtop 补齐流程）
  - `src/xianyu_mcp/first_run_setup.py`（依赖二维码状态推进来驱动 UI 与写入）
- 外部接口：不新增/不破坏现有 MCP 工具签名（行为更稳定、日志更清晰）

