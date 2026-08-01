## Context

当前项目已支持通过环境变量读取 Cookie（`XIANYU_COOKIE` / `XIANYU_COOKIE_FILE`），并在缺少 Cookie 时提供“首次配置模式”（本机网页展示二维码 + 扫码写入 `.env`）。但在 Trae 客户端使用时，用户仍可能需要编辑 `.env` 或复制 Cookie 文件路径，体验不如 GitHub MCP “在配置界面直接输入 Token”。

Trae 的 MCP Server 配置来源是工作区内的 `.trae/mcp.json`。当其中存在 `env` 配置项时，Trae 会在 UI 中渲染对应的输入框，用户在 UI 内填写即可随进程环境变量启动服务端。

## Goals / Non-Goals

**Goals:**

- 在工作区自带的 `.trae/mcp.json` 中为 `xianyu-mcp-server` 增加可填写的环境变量项，使用户能在 Trae 的配置界面直接输入 Cookie（文本框）完成首次配置。
- 明确并文档化 Cookie 的读取优先级：进程环境变量优先于 `.env`，并保留 `XIANYU_COOKIE_FILE` 作为更易管理的方案。
- 不引入新的网络流程、不改动闲鱼接口调用；仅改善接入与配置体验。

**Non-Goals:**

- 不实现 Trae 客户端侧的自定义 UI（例如专门的二维码弹窗/内嵌浏览器）。服务端仅提供 env 配置与首次配置网页。
- 不增加新的鉴权/加密存储机制（由客户端配置存储策略决定）。

## Decisions

- **Decision: 通过 `.trae/mcp.json` 的 `env` 来触发 Trae UI 输入框**
  - Why: 与 GitHub MCP 的使用方式一致；无需新协议；对其它 MCP 客户端无侵入。
  - Alternative: 增加服务端“set_cookie”工具写 `.env`。该方式仍需要先能调用工具且 UI 不一定提示输入框，不满足“像 GitHub 一样的初次配置”诉求。

- **Decision: 保留 `XIANYU_COOKIE_FILE` 并在 UI 同时提供**
  - Why: Cookie 字符串较长，文件方式更利于管理/更新；且可将文件放到已 gitignore 的目录降低误提交风险。

- **Decision: 默认不在仓库内写入真实 Cookie**
  - Why: 避免敏感信息进入版本控制。仓库内仅提供空占位/示例键名，真实值由用户在 Trae UI 中填写。

## Risks / Trade-offs

- **[Risk] Trae 客户端把 env 值回写到 `.trae/mcp.json` 导致误提交** → Mitigation：README 明确提示不要提交含 Cookie 的变更；推荐使用 `XIANYU_COOKIE_FILE` 指向一个被 gitignore 的文件路径。
- **[Risk] 不同 MCP 客户端不支持 env 输入 UI** → Mitigation：该变更不影响其它客户端；其它客户端继续使用 `.env` 或 shell env。
- **[Trade-off] 文本框输入 Cookie 依然需要用户自行获取 Cookie** → Mitigation：与既有“首次配置模式（二维码）”互补；用户可二选一。

