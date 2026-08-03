## Context

- 目标接口来自 `DoLovya/XianYuClient` 的 `GetUserPageNavDataAsync` 实现：
  - MTop API：`mtop.idle.web.user.page.nav`
  - URL：`https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/`
  - `data`：`{}`
- 本仓库已具备通用的 MTop 签名与请求封装（`third_party/pyxianyu/core/client.py`），可复用同一套签名通道。

## Goals / Non-Goals

**Goals:**

- 新增 `get_my_profile`，让 MCP 层可以获取“当前登录用户”的个人页数据。
- 返回以 `raw` 为主（完整响应），并提供尽力提取的结构化字段，便于直接展示/消费。
- 工具必须走 `RequestGuardrails.run_read`，避免高频调用导致风控。

**Non-Goals:**

- 不保证所有字段都能稳定提取（闲鱼存在 AB 实验与字段变动），结构化字段以“尽力而为”为原则。
- 不在本变更中扩展到“指定 user_id 的他人主页信息”（需要额外接口与风控评估）。

## Decisions

- **API 封装层：新增 `UserApi`**
  - 选择：在 `third_party/pyxianyu/apis/` 新增 `user_api.py`（或同名文件）。
  - 原因：职责清晰，避免继续膨胀 `auth_api.py` / `item_api.py`。
- **输出格式：raw 永远返回**
  - 选择：`get_my_profile` 返回 `{ success, profile, raw }`。
  - 原因：接口响应结构复杂且可能变动，raw 便于快速适配；profile 便于日常直接使用。
- **限速策略：读操作**
  - 选择：所有请求通过 `run_read` 执行。
  - 原因：个人信息查询属于读操作，但可能被 UI/Agent 高频调用，必须受读限速保护。

## Risks / Trade-offs

- [字段变动] → 以 raw 为主；结构化字段提取“缺字段不报错”。
- [_m_h5_tk 缺失/过期] → 沿用现有 client 行为：缺 token 会抛配置错误；MCP 侧透出明确错误信息。
- [风控] → 强制走 guardrails read；不新增并发/批量用户信息抓取能力。
