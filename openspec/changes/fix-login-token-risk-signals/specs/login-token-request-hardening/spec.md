## ADDED Requirements

### Requirement: 毫秒级精度时间戳
`XianyuClient.build_mtop_params` 生成的 `t` 参数 SHALL 为自 1970-01-01 UTC 以来的**毫秒级时间戳**（13 位十进制），调用当次返回值的末三位不恒等于 `000`。该值 SHALL 直接参与 `generate_sign` 的签名输入。

#### Scenario: 连续调用 t 有差异且末三位非 000
- **WHEN** 在同一次 Python 进程中连续 100 次调用 `build_mtop_params` 取其 `t` 值
- **THEN** 100 个 `t` 中至少 95 个的末三位不全为 `000`
- **AND** 相邻调用的 `t` 差值在 `[0, 2000]` 毫秒区间（反映真实时钟流逝）

#### Scenario: 签名输入值与实际时间一致
- **WHEN** `build_signed_form(params, data)` 在调用时传入刚生成的 `params`
- **THEN** 参与 `generate_sign(t, token, data)` 的 `t` 与 `params["t"]` 完全相等，无任何精度缩放

---

### Requirement: 稳定且账号相关的 device_id
`generate_device_id(user_id)` SHALL 在同一 `user_id`（unb）输入下**返回完全相同的字符串**（跨进程、跨调用、跨天）。返回格式 SHALL 保留「UUID-like 段 + '-' + user_id」的结构，保持与既有字段形态的兼容性。

#### Scenario: 同一 unb 多次调用返回相同
- **WHEN** 输入 `user_id="2206538887867"`，连续调用 100 次
- **THEN** 所有返回值字符串完全相等，无任何随机波动

#### Scenario: 不同 unb 返回不同
- **WHEN** 分别以 `user_id="A"` 和 `user_id="B"`（A≠B）调用
- **THEN** 两次返回的 device_id 字符串 SHALL 不相等（哈希冲突可忽略）

#### Scenario: 结果后段携带 unb 后缀
- **WHEN** 任意 unb 调用 `generate_device_id`
- **THEN** 返回值 SHALL 以 `"-" + unb` 结尾

---

### Requirement: get_token 默认 TLS 校验
调用 `AuthApi.get_token` 发起的 HTTP 请求 SHALL **不跳过 TLS 证书校验**，与 `refresh_token` 使用同一校验策略（requests 默认 `verify=True`）。请求 SHALL 不再传入 `verify=False`。

#### Scenario: get_token 使用 verify True
- **WHEN** 调用 `get_token`，拦截底层 session.post 的 `verify` 参数
- **THEN** 传入的 `verify` SHALL 为 `None` 或 `True`，SHALL NOT 为 `False`

#### Scenario: refresh_token 与 get_token 校验策略一致
- **WHEN** 对比 refresh_token 请求与 get_token 请求的 verify 参数
- **THEN** 两者 SHALL 均使用 `True` 或 `None`，策略一致

---

### Requirement: get_token 单次尝试不绕过 guardrails
`AuthApi.get_token` 对底层 HTTP 请求的尝试次数 SHALL 为 1 次。失败应直接向上抛异常，使外层 guardrails（`run_read_async` 等）能正确捕获单次调用失败并计入 backoff / cooldown。

#### Scenario: 响应 FAIL_SYS_USER_VALIDATE 单次即抛
- **WHEN** 服务端返回 `FAIL_SYS_USER_VALIDATE`
- **THEN** `get_token` 在 1 次尝试后 SHALL 立即抛异常，不进行内部重试
- **AND** 该异常 SHALL 被 guardrails._is_strong_risk_error 识别并触发 cooldown（冷却）

#### Scenario: 多次失败由 guardrails 退避调度
- **WHEN** 连续多次从外层 MCP Tool 调用 `validate_login`（每次都失败）
- **THEN** 调用 SHALL 依次被 guardrails 拉长 backoff 间隔（2^n 秒），而不是在 1 次 Tool 调用内发 3 次 HTTP 请求

---

### Requirement: get_token 不显式构造 Host 头
`AuthApi.get_token` 调用 `build_json_headers` SHALL 不传 `include_host` 参数（使用默认 False），让 requests 依据 URL 自动产生 Host 头。

#### Scenario: 无多余 Host 头
- **WHEN** `get_token` 发起请求时构造 headers
- **THEN** 返回的 headers 中 SHALL **不含** `"Host"` 键
- **AND** 请求实际发出的 Host（由 requests 自动生成）SHALL 与目标 URL 域名一致

#### Scenario: 与 refresh_token 请求头策略一致
- **WHEN** 对比 `refresh_token` 与 `get_token` 的 headers 构成
- **THEN** 两者 SHALL 均由 `build_json_headers()`（无 include_host 参数调用）生成，Host 头处理策略一致
