## Why

调用 `get_token`（`mtop.taobao.idlemessage.pc.login.token`）接口时即使 Cookie 本身有效，仍高频触发 `FAIL_SYS_USER_VALIDATE` + `RGV587_ERROR::SM` 风控，导致 `validate_login`、`list_conversations`、消息拉取等依赖 WS 握手的功能完全不可用。而 `refresh_token`（`loginuser.get`）可正常返回，证明 Cookie、频率控制（guardrails）均正常。根因是请求形态存在明显脚本指纹，被闲鱼风控模型识别。现在修复以消除这些指纹。

## What Changes

- 修复 `build_mtop_params` 中 `t` 的精度：从「秒级时间戳 × 1000（末三位恒 000）」改为真正的毫秒级时间戳
- 修复 `generate_device_id`：从每次 UUID4（永新设备）改为基于 `unb` 的确定性哈希（同账号稳定），避免被判定为异常多设备登录
- 修复 `AuthApi.get_token` 的 `verify=False`：改为 `verify=None`（保持默认 True，正常 TLS 握手，与 `refresh_token` 一致）
- 修复 `AuthApi.get_token` 的重试策略：去除绕过 guardrails 的内部 `max_attempts=3` 紧循环重试，改为外层 guardrails 接手退避
- 修复 `AuthApi.get_token` 中 `include_host=True` 多余的 Host 头：改为默认 False，避免双 Host/畸形请求特征
- 同步更新 `third_party/pyxianyu` 中对应模块，保持子项目与本项目一致

## Capabilities

### New Capabilities
- `login-token-request-hardening`：为 `AuthApi.get_token`、`build_mtop_params`、`generate_device_id` 等底层请求组件建立「浏览器等价」的指纹约束，覆盖时间戳、device_id、TLS 校验、请求头、重试策略

### Modified Capabilities
（无，本次变更全部为实现细节修复，未改变对外接口或业务行为语义）

## Impact

- 受影响文件：
  - `third_party/pyxianyu/src/pyxianyu/core/client.py`（build_mtop_params）
  - `third_party/pyxianyu/src/pyxianyu/utils/xianyu_utils.py`（generate_device_id）
  - `third_party/pyxianyu/src/pyxianyu/apis/auth_api.py`（get_token）
- 影响面：所有通过 `get_token` 进行 WS 握手的功能（`validate_login`、`list_conversations`、消息收发等）
- 向后兼容：无任何 BREAKING 改动，对外 API 参数/返回完全不变
- 依赖：无新增依赖
