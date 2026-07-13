# XianYuApis MCP

基于 `third_party/XianYuApis` 封装的闲鱼 MCP 服务。

当前已提供这些工具：

- `validate_login`：校验 Cookie 是否还能换到 `accessToken`
- `refresh_login`：刷新登录态
- `get_item_detail`：查询商品详情
- `list_my_items`：读取当前登录账号名下的全部商品列表
- `list_conversations`：读取当前账号最近会话列表
- `list_conversation_messages`：读取指定会话历史消息
- `send_text_message`：主动发送文本消息
- `send_image_message`：主动发送图片消息

## 目录说明

```text
xianyu-mcp-server/
├── .mcp/XianYuApis_MCP/
│   ├── server.py
│   ├── pyproject.toml
│   ├── .env.example
│   └── tools/xianyu_api_tools.py
└── third_party/XianYuApis/
```

## 环境要求

- Node.js 18+
- `uv`
- 闲鱼登录后的完整 Cookie

## 初始化

```bash
cd .mcp/XianYuApis_MCP
cp .env.example .env
```

然后填写：

```env
XIANYU_COOKIE=你的完整闲鱼 Cookie
```

## 安装依赖

```bash
uv sync
```

## 本地启动

```bash
uv run server.py
```

## Trae 项目级接入

把下面这段配置加到项目根目录的 `.trae/mcp.json`：

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

## 当前边界

首版优先做短调用工具，不包含常驻监听和自动回复主循环。
如果下一步要接 AI 自动客服，建议单独补一个“消息监听 Worker”，不要直接塞进 MCP 主进程。

## 相关文档

- 商品列表接口记录：[`../../docs/mtop_idle_web_xyh_item_list.md`](../../docs/mtop_idle_web_xyh_item_list.md)
