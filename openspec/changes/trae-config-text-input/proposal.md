## Why

当前闲鱼 MCP 的首次可用状态依赖 `XIANYU_COOKIE`。现状需要用户编辑 `.env` 或从浏览器复制 Cookie，流程繁琐且易出错。希望像 GitHub MCP 一样，在 Trae 的 MCP Server 配置界面直接通过文本框输入 Cookie（写入 `env`），即可完成首次配置与后续使用。

## What Changes

- 在工作区自带的 `.trae/mcp.json` 中为 `xianyu-mcp-server` 增加 `env` 配置项，使 Trae 客户端在添加/配置 MCP Server 时可直接通过文本框填写：
  - `XIANYU_COOKIE`
  - `XIANYU_COOKIE_FILE`（可选，指向本地文件路径）
- 明确优先级与安全约束：运行时优先使用进程环境变量（客户端配置），避免把敏感 Cookie 提交到仓库。
- 更新 README，新增 Trae 客户端配置示例与建议实践。

## Capabilities

### New Capabilities

- `trae-config`: 支持通过 Trae MCP Server 配置界面（`mcp.json` 的 `env`）输入 Cookie 或 Cookie 文件路径完成首次配置。

### Modified Capabilities

无。

## Impact

- 配置文件：`.trae/mcp.json`（新增 `env` 字段，默认留空）
- 文档：`README.md`（新增 Trae 配置说明）
- 不修改闲鱼 API 能力本身；仅优化“首次配置/接入”体验
