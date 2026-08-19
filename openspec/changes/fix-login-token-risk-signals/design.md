## Context

闲鱼 MCP 通过两层链路调用闲鱼接口：
- 宽松链路：HTTP mtop API，如 `refresh_login`（`mtop.taobao.idlemessage.pc.loginuser.get`）
- 严格链路：HTTP `get_token`（`mtop.taobao.idlemessage.pc.login.token`，生成 WS 握手 accessToken）→ 之后才是长连接 WS

当前问题集中在严格链路 `get_token`：即便 refresh_login 成功（Cookie / userId 有效），`get_token` 仍稳定返回 `FAIL_SYS_USER_VALIDATE + RGV587_ERROR::SM`（风控拦截，SM 通常是滑动/人脸验证）。

已知 guardrails 已提供 read/write 间隔、backoff、cooldown，且实际调用频率远低于阈值，排除「频率问题」。通过请求形态对比确认：问题集中在**浏览器 vs 脚本的指纹差异**，共有 5 个已确认差异点（见 proposal）。

本项目 third_party/pyxianyu 是 vendored，改动需保持签名/接口行为不影响上层 xianyu_api_tools（仅内部实现变更）。

## Goals / Non-Goals

**Goals:**
- 消除 `get_token` 请求的所有已识别脚本指纹，使其在 TLS、HTTP、签名 3 个层面与浏览器在 goofish.com 上的实际请求等价或无法区分
- `generate_device_id` 在同一 `unb`（同一账号）上产生稳定输出，避免被标记为「永新设备」
- `build_mtop_params` 的 `t` 为真实毫秒时间戳（末三位不恒 000）
- `get_token` 不在 guardrails 外做紧循环重试；重试策略统一交由外层 guardrails
- 零 BREAKING：所有上层 API 参数、返回结构、接口名不变
- 修复后 `list_conversations(only_top=True)` 在风控解除后可以正常返回

**Non-Goals:**
- 不解封已被闲鱼标记的账号（由浏览器端完成滑块/人脸解除）
- 不改变 guardrails 的配置与行为（read_min_interval / cooldown 等保持默认）
- 不引入新的外部 HTTP 客户端（仍使用 requests）
- 不修改业务逻辑（WS 消息编解码、conversation 归一化、only_top 过滤等全部不变）
- 不处理 third_party 之外的 pyxianyu 上游项目

## Decisions

### D1. `t` 时间戳精度：改为真实毫秒

**决策**：`build_mtop_params` 中的 `"t": str(int(time.time()) * 1000)` 改为 `str(int(time.time() * 1000))`。

**Rationale**：
- 末三位恒 000 是最强脚本识别信号之一；闲鱼服务端对 `t` 的格式与签名精度均会校验。当前写法即便能通过签名，格式也异常。
- 影响面很小：只改一行，不改变签名公式（仍为 md5(token&t&salt&data)），只改变 t 的输入值。
- 备选方案不改精度直接加 `random.randint(0,999)`：虽也能让末三位非 0，但与真实时间仍不匹配，可能被其他维度判定异常；直接用真实毫秒最佳。

**备选**：
- 备选 B：构造 t 为「真实毫秒 + 随机小抖动」。REJECTED：真实毫秒已满足需求，抖动反而可能引入时序异常。

### D2. device_id 稳定性：基于 unb 的确定性哈希

**决策**：`generate_device_id(user_id)` 从 `uuid4()+unb` 改为 `md5(unb).hexdigest()` 按 8-4-4-4-12 切分后拼接 `-{unb}`。

**Rationale**：
- 同账号（同 unb）得到稳定 device_id，与浏览器持久化 device_id 的行为一致。
- 无需新增持久化存储（env、文件），对多环境部署、容器友好。
- 格式仍为 UUID-like 结构，与原形态兼容，上层无需变更。
- 备选 A（.env 配置 `XIANYU_DEVICE_ID`）：需要用户额外配置，且 unb 不同时要手动维护，体验差。
- 备选 B（本地文件缓存 `~/.xianyu/device_id.json`）：对 CLI 工具是好方案，但 MCP 运行时可能无 HOME 写权限；哈希方案 0 副作用。

**备选**：
- 备选 C：混合，哈希 + env 覆盖（有 env 用 env，无 env 用哈希）。可后续再加，本次哈希已足够。

### D3. `verify`：`get_token` 去掉 `verify=False`，与 `refresh_token` 一致

**决策**：`AuthApi.get_token` 中的 `verify=False` 改为 `verify=None`（不传入，即使用 requests 默认 `True`）。

**Rationale**：
- `refresh_token`（没传 verify，默认 True）可以过、`get_token`（`verify=False`）不行，二者唯一差异即此；直接对齐即可。
- `verify=False` 会抑制证书校验，SSL 握手期间产生的 JA3/JA4 指纹与浏览器完全不同，闲鱼服务端大概率有 TLS 指纹库匹配。
- 备选：保持 verify=False 但加 urllib3 配置更完整的 cipher 套件。REJECTED：无法匹配浏览器的 JA3，且需要引入复杂 cipher 配置，风险高。

### D4. get_token 重试策略：去掉内部紧循环重试，让外层 guardrails 退避

**决策**：`AuthApi.get_token` 的 `max_attempts` 从 3 改为 1；或等价地直接调一次，不做内部 retry。让外层的 guardrails（backoff + cooldown）统一处理失败重推。

**Rationale**：
- 当前 3 次 attempt 之间无间隔（代码里每次 attempt ≈ 0.2s 以内），对风控系统来说就是「同一异常请求短时间猛冲」。
- guardrails.run_read_async 已经包含 backoff：失败次数每 +1 就 2^n 秒递增 backoff。正确做法是：外层失败 → backoff → 再次调用 XianYuApiTools.validate_login（或 list_conversations），而不是在 get_token 内部做「伪重试」。
- 备选：内部 attempt 之间加 `time.sleep(1+jitter)`。REJECTED：仍会突破 guardrails 的统计，使 backoff / cooldown 感知不到实际次数。

### D5. Host 头：include_host=False

**决策**：`AuthApi.get_token` 的 `build_json_headers(include_host=True)` 改为 `include_host=False`，与 `refresh_token` 一致。

**Rationale**：
- requests 默认会自动生成 Host。requests 文档明确「用户不要手动设置 Host」，因为它由 URL+连接层决定。手动加会：
  1. 某些场景下产生双 Host 头（畸形）；
  2. 在通过代理 / IPv6 / SNI 等握手形态时，手写 Host 和 requests 内部计算的 Host 可能有细微大小写/尾点差异，风控会把这些看作非浏览器请求。
- `refresh_token` 不加 Host 头可以正常通过，直接对齐。

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| D2：device_id 变更为稳定值后，如果当前账号当前「已生成的 device_id」被闲鱼标记了（虽然极不可能），新的稳定 ID 会重置标记 | 哈希确定性可复现；即使重标记也能通过改变盐值（或加 env）再换一次，远比每次都换新的好 |
| D3：去掉 verify=False 后，如本地系统 CA 有问题（公司代理 / MITM）可能会 TLS 报错 | 在 pyproject.toml 或 docs/troubleshooting.md 中补充 REQUESTS_CA_BUNDLE / CURL_CA_BUNDLE 两种变量指引；本次先不改文档（遵循「NEVER 主动加文档」） |
| D4：去掉内部 attempt，短期可能让调用者对失败更敏感（之前 3 次中 1 次成功就显示 OK） | 现在单次失败即抛错，但 guardrails 有 backoff，下次再次调用仍能按 2^n 退避；反而让错误能被 guardrails._on_error 正确计数 |
| D5：去掉 Host 头后在极个别 requests 老版本 + 老 Python 上可能默认 Host 生成不是 utf-8 | 当前项目限定 Python≥3.11，requests 在 pyproject.toml 中 ≥2.33；已无此问题 |
| 账号已被 `RGV587_ERROR::SM` 硬标记 → 修完指纹后仍需要浏览器端解除 | 变更方案说明里明确：修指纹是降低拦截概率；解除标记需要用户浏览器端走一次 goofish.com 完成滑块/人脸或扫码登出后再登录 |

## Migration Plan

无数据库、无 schema 变更。直接部署：
1. 应用 5 处代码修复。
2. AST + 语法 + 导入验证。
3. 让用户在浏览器端 goofish.com 登录同一账号完成一次滑块/人脸（如仍被拦），或用 QR 登录（qx_login_generate/status/save_env）获取全新 Cookie。
4. 重新调用 `list_conversations(only_top=True)` 验证。

回滚：任何一处修复导致接口整体异常，直接 git revert。因为只改 third_party/pyxianyu 内部实现，上层不受影响。

## Open Questions

无。
