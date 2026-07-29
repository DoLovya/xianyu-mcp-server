## ADDED Requirements

### Requirement: 请求护栏（Request Guardrails）
系统 SHALL 在调用闲鱼接口前执行统一的请求护栏策略，以降低触发风控的概率并避免风控后的进一步恶化。

### Requirement: 工具分级限速
系统 SHALL 将 MCP 工具分为只读与写操作两类，并应用不同的最小调用间隔与随机抖动：

- 只读工具（READ）：`validate_login`、`refresh_login`、`list_my_items`、`get_item_detail`、`get_item_edit_detail`、`list_conversations`、`list_conversation_messages`
- 写工具（WRITE）：`publish_physical_item`、`edit_item`、`downshelf_item`、`reshelf_item`、`send_text_message`、`send_image_message`

系统 SHALL 支持通过环境变量配置 READ/WRITE 的最小间隔与抖动范围，并提供保守的默认值。

#### Scenario: READ 限速与抖动
- **WHEN** 客户端连续调用 READ 工具
- **THEN** 系统在每次实际请求前确保距离上一次 READ 请求至少经过 `read_min_interval` 秒
- **THEN** 系统在 `read_min_interval` 的基础上附加 `0 ~ read_jitter` 的随机抖动

#### Scenario: WRITE 串行与限速
- **WHEN** 客户端连续调用 WRITE 工具
- **THEN** 系统 SHALL 串行执行写操作请求（同一进程内不可并发写）
- **THEN** 系统在每次实际请求前确保距离上一次 WRITE 请求至少经过 `write_min_interval` 秒
- **THEN** 系统在 `write_min_interval` 的基础上附加 `0 ~ write_jitter` 的随机抖动

### Requirement: 指数退避
系统 SHALL 在遇到可疑失败（网络失败、5xx、或明确风控信号）时启用指数退避，避免立即重试造成“连击”特征。

#### Scenario: 可疑失败触发退避
- **WHEN** 某次请求失败，且错误被判定为“可疑失败”
- **THEN** 系统为后续请求设置退避时间窗，退避时长 SHALL 随连续失败次数指数增长，并带随机抖动

### Requirement: 熔断与冷却
系统 SHALL 在检测到强风控信号时触发熔断，并进入冷却期，在冷却期内拒绝写操作请求。

#### Scenario: `FAIL_SYS_USER_VALIDATE` 触发熔断
- **WHEN** 任意工具调用返回 `FAIL_SYS_USER_VALIDATE` 或等价的强风控信号
- **THEN** 系统 SHALL 进入冷却期
- **THEN** 冷却期内所有 WRITE 工具调用 SHALL 被拒绝，且不会向闲鱼发起实际请求
- **THEN** 系统向客户端返回明确的错误信息，提示“风控冷却中/需要人工验证或更新 Cookie”

### Requirement: 配置与安全
- 系统 SHALL 允许通过环境变量调整护栏参数（READ/WRITE 限速、抖动、退避上限、冷却时长）
- 系统 MUST NOT 在日志或错误消息中输出 Cookie、token、或其他敏感字段
