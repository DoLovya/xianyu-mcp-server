# xianyu-mcp-server

基于 `third_party/XianYuApis` 封装的闲鱼 MCP 项目，用于把闲鱼商品、会话、消息发送等能力接入支持 MCP 的客户端。

## 🛡 注意事项

> [!WARNING]
> 本项目为开源项目，请在遵守相关法律法规与平台规则的前提下使用。
>
> 鉴于项目的特殊性，开发团队可能在任何时间停止更新或删除项目。

## 📄 使用协议

本项目采用 `GNU GPL v3.0` 协议。

- 允许：学习、修改、分发与再发布
- 要求：衍生作品在分发时需继续遵循 GPL v3.0 条款
- 提示：第三方依赖或子模块如有单独协议，以其各自协议为准

详细条款见 [`LICENSE`](./LICENSE)。

当前仓库分成两层：

- `third_party/XianYuApis`：闲鱼底层 HTTP / WebSocket 能力
- `.mcp/XianYuApis_MCP`：面向 MCP 的工具封装

## ✨ 功能清单

- 🔐 `validate_login`：校验当前 Cookie 是否有效
- 🔄 `refresh_login`：刷新当前登录态
- 🛍️ `get_item_detail`：获取商品详情
- 🧾 `list_my_items`：读取当前登录账号名下的全部商品列表
- 📋 `list_conversations`：读取当前账号最近会话列表
- 💬 `list_conversation_messages`：读取指定会话历史消息
- ✉️ `send_text_message`：主动发送文本消息
- 🖼️ `send_image_message`：主动发送图片消息
- ✅ 已验证可读取当前登录用户 `userId`
- ✅ 已验证可拉取当前账号的商品列表
- ✅ 已验证可通过个人主页接口拿到自己的商品分页数据

## 🚀 当前能力

当前 MCP 已开放这些工具：

- `validate_login`：校验当前 Cookie 是否有效
- `refresh_login`：刷新当前登录态
- `get_item_detail`：获取商品详情
- `list_my_items`：读取当前登录账号名下的全部商品列表
- `list_conversations`：读取当前账号最近会话列表
- `list_conversation_messages`：读取指定会话历史消息
- `send_text_message`：主动发送文本消息
- `send_image_message`：主动发送图片消息

当前项目已经验证过这些能力：

- 能读取当前登录用户 `userId`
- 能拉取当前账号的商品列表
- 能通过个人主页接口拿到自己的商品分页数据

## 🚧 当前边界

当前版本优先支持短调用工具，暂未做这些能力的 MCP 化：

- 扫码登录
- 常驻监听消息
- 自动回复 Worker
- 媒体上传独立 MCP 工具

如果后续要接 AI 自动客服，建议把“消息监听”和“MCP 短调用”拆成两个进程，不要把常驻循环直接塞进 MCP 主进程。

## 🗂️ 目录结构

```text
xianyu-mcp-server/
├── .mcp/
│   └── XianYuApis_MCP/
│       ├── server.py
│       ├── pyproject.toml
│       ├── README.md
│       └── tools/
│           └── xianyu_api_tools.py
├── .trae/
│   └── mcp.json
├── third_party/
│   └── XianYuApis/
└── README.md
```

## 🧰 环境要求

- Python 3.11+
- Node.js 18+
- `uv`
- 闲鱼登录后的完整 Cookie

## ⚙️ 初始化

先拉取子模块：

```bash
git submodule update --init --recursive
```

然后准备 MCP 环境变量：

```bash
cd .mcp/XianYuApis_MCP
cp .env.example .env
```

填写：

```env
XIANYU_COOKIE=你的完整闲鱼 Cookie
```

## 📦 安装依赖

```bash
uv sync --directory .mcp/XianYuApis_MCP
```

## ▶️ 本地启动 MCP

```bash
uv run --directory .mcp/XianYuApis_MCP server.py
```

默认使用 `stdio` 传输。  
如需 HTTP 模式：

```bash
uv run --directory .mcp/XianYuApis_MCP server.py --http
```

## 🔌 Trae 接入

在项目根目录创建或修改 `.trae/mcp.json`：

```json
{
  "mcpServers": {
    "XianYuApis": {
      "command": "uv",
      "args": [
        "--directory",
        "${workspaceFolder}/.mcp/XianYuApis_MCP",
        "run",
        "server.py"
      ]
    }
  }
}
```

配置完成后，重载 Trae 或重新打开工作区。

## ❓ 常见问题

### 1. Trae 检测不到闲鱼 MCP

通常是因为项目根目录没有 `.trae/mcp.json`，或者 `mcpServers` 里没有注册 `XianYuApis`。

### 2. MCP 调用时报未配置 Cookie

确认 `.mcp/XianYuApis_MCP/.env` 中已经配置：

```env
XIANYU_COOKIE=...
```

如果是 Trae 已经加载过旧进程，修改后需要刷新 MCP。

### 3. 为什么仓库里有接口，但 MCP 没有工具

`third_party/XianYuApis` 是底层能力库，`.mcp/XianYuApis_MCP` 只封装了其中一部分高频场景。  
当前并不是“底层所有 API 都自动暴露到 MCP”。

## 📚 相关文档

- MCP 封装说明：[`./.mcp/XianYuApis_MCP/README.md`](./.mcp/XianYuApis_MCP/README.md)
- 底层项目说明：[`./third_party/XianYuApis/README.md`](./third_party/XianYuApis/README.md)
- 商品列表接口记录：[`./docs/mtop_idle_web_xyh_item_list.md`](./docs/mtop_idle_web_xyh_item_list.md)
