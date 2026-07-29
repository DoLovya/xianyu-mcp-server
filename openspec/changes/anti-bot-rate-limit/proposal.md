## Why

当前 MCP 服务在连续执行多次读/写操作后容易触发闲鱼风控（例如 `FAIL_SYS_USER_VALIDATE`），导致后续所有能力不可用且需要人工重新获取 Cookie。需要在工具层引入“节流 + 抖动 + 退避”的调用约束，降低自动化特征与请求频率。

## What Changes

- 为所有闲鱼 MCP 工具引入统一的请求护栏（Request Guardrails）：限速、随机抖动、指数退避、写操作串行化
- 在检测到风控信号时执行熔断与冷却：短时间内阻止进一步写操作，避免“连击”导致更严格拦截
- 提供可配置的策略参数（环境变量），便于按账号/网络环境调整

## Capabilities

### New Capabilities

- `request-guardrails`: 为 MCP 工具调用闲鱼接口提供统一的限速/抖动/退避/熔断能力，并对外暴露可配置策略

### Modified Capabilities

- 无

## Impact

- 影响代码：
  - `src/xianyu_mcp/tools/xianyu_api_tools.py`（在所有工具调用前后接入护栏逻辑）
  - 可能新增 `src/xianyu_mcp/` 下的护栏模块（如 rate limit / cooldown 状态管理）
- 影响行为：部分工具调用会被主动延迟或拒绝（冷却中）以保护账号
- 影响配置：新增若干环境变量用于调参（默认值提供开箱可用的保守策略）
