## Why

当前 MCP 工具集缺少“获取当前登录用户个人信息”的能力，导致无法在自动化场景中：

- 对外展示账号信息（昵称/头像/地区等）
- 在消息/商品等场景做更完整的上下文（例如“卖家是谁”）
- 做后续扩展（例如店铺页数据、个人页导航、账号状态诊断）

`DoLovya/XianYuClient` 已实现对应的个人页数据接口调用（`mtop.idle.web.user.page.nav`），可作为本仓库新增能力的接口基线。

## What Changes

- 在 `third_party/pyxianyu` 增加用户相关 API 封装（最小实现：获取个人页导航数据）。
- 在 MCP 层新增只读工具 `get_my_profile`：
  - 返回结构化字段（尽力提取）+ 原始响应 `raw`（完整透传，便于快速适配）。
- 增加回归测试，覆盖“工具可调用 + 返回结构符合约定”。

## Capabilities

### New Capabilities

- `user-profile`: 获取当前登录用户的个人信息/个人页导航数据（以 `raw` 为主，结构化字段为辅）。

### Modified Capabilities

- （无）

## Impact

- `third_party/pyxianyu`：新增 `UserApi`（或同职责文件），实现 `mtop.idle.web.user.page.nav` 调用。
- `src/xianyu_mcp`：新增 MCP 工具 `get_my_profile`，通过 guardrails 的 read 通道执行。
- `tests/`：新增/扩展测试用例，保证工具注册与输出格式稳定。
