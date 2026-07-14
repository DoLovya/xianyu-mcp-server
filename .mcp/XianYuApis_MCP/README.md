# XianYuApis MCP

基于 `third_party/XianYuApis` 封装的闲鱼 MCP 服务。

当前已提供这些工具：

| 工具名 | 说明 |
| --- | --- |
| `validate_login` | 校验 Cookie 是否还能换到 `accessToken` |
| `refresh_login` | 刷新登录态 |
| `get_item_detail` | 查询商品详情 |
| `get_item_edit_detail` | 查询商品在 PC 编辑页的编辑详情 |
| `list_my_items` | 读取当前登录账号名下的全部商品列表 |
| `downshelf_item` | 下架当前登录账号名下的指定商品 |
| `reshelf_item` | 通过 PC 编辑重发布链路重新上架指定商品 |
| `list_conversations` | 读取当前账号最近会话列表 |
| `list_conversation_messages` | 读取指定会话历史消息 |
| `send_text_message` | 主动发送文本消息 |
| `send_image_message` | 主动发送图片消息 |

其中商品管理相关能力目前分两层：

- MCP 已直接暴露：`get_item_detail`、`get_item_edit_detail`、`list_my_items`、`downshelf_item`、`reshelf_item`
- 底层库已实现但尚未单独暴露为 MCP：`prepublish_check`、`preget`、`edit_item`、`build_reshelf_payload`

关于上下架能力，当前建议按下面理解：

- `downshelf_item`：可用于普通商品下架
- `reshelf_item`：适用于支持 PC 编辑链路的已存在商品重上架
- 虚拟商品目前通常受闲鱼 PC 端发布管控影响，无法通过当前 MCP 重上架
- 支持 PC 编辑的实物商品，当前已验证可下架、可重新上架

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

也支持改为文件方式：

```env
XIANYU_COOKIE_FILE=./cookie.txt
```

`XIANYU_COOKIE` 与 `XIANYU_COOKIE_FILE` 二选一即可。

## 安装依赖

```bash
uv sync
```

## 本地启动

```bash
uv run server.py
```

如需 HTTP 模式：

```bash
uv run server.py --http
```

`server.py` 会在每次工具调用前重新读取 `.env`。如果你修改了 Cookie，但 MCP 客户端仍复用旧进程，建议同时在客户端里重载一次该服务。

## Trae 项目级接入

把下面这段配置加到项目根目录的 `.trae/mcp.json`：

```json
{
  "mcpServers": {
    "xianyuapis": {
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

`xianyuapis` 只是示例服务名，可按需自定义。

## 推荐验证顺序

1. `validate_login`：先确认 Cookie 仍然有效
2. `list_my_items`：确认能拉到当前账号商品
3. `get_item_detail` / `get_item_edit_detail`：确认商品查询链路正常
4. `downshelf_item` / `reshelf_item`：最后再执行变更类操作

## 当前边界

首版优先做短调用工具，不包含常驻监听和自动回复主循环。
如果下一步要接 AI 自动客服，建议单独补一个“消息监听 Worker”，不要直接塞进 MCP 主进程。

当前 `reshelf_item` 走的是“编辑详情 -> 构造 payload -> edit 重发布”的封装链路；如果后续要支持“全新发布商品”，还需要继续把 `prepublish_check`、`preget` 与发布参数构造过程 MCP 化。

另外，`reshelf_item` 是否可用不仅取决于当前仓库实现，也取决于闲鱼是否允许该商品走 PC 端编辑/发布：

- 若接口返回 `FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT`，通常表示该商品只能在闲鱼 App 内发布或编辑
- 当前实测下，虚拟商品通常属于这一类限制对象

## 相关文档

- 商品列表接口记录：[`../../third_party/XianYuApis/docs/mtop_idle_web_xyh_item_list.md`](../../third_party/XianYuApis/docs/mtop_idle_web_xyh_item_list.md)
- 商品下架接口记录：[`../../third_party/XianYuApis/docs/mtop_taobao_idle_item_downshelf.md`](../../third_party/XianYuApis/docs/mtop_taobao_idle_item_downshelf.md)
- 商品预发布检查接口记录：[`../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_prepublish_check.md`](../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_prepublish_check.md)
- 商品预取发布参数接口记录：[`../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_preget.md`](../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_preget.md)
- 商品编辑详情接口记录：[`../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit_detail.md`](../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit_detail.md)
- 商品编辑重发布接口记录：[`../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit.md`](../../third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit.md)
