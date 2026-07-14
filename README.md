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

## ✨ 项目概览

当前仓库分成两层：

- `third_party/XianYuApis`：闲鱼底层 HTTP / WebSocket 能力
- `.mcp/XianYuApis_MCP`：面向 MCP 的工具封装

适合的使用场景：

- 在 Trae、Cherry Studio、Claude Desktop 等支持 MCP 的客户端中直接调用闲鱼能力
- 把闲鱼卖家工作流接入自定义 Agent / 工作流编排系统
- 作为后续自动客服、消息分发、店铺运维脚本的基础设施

## 🚀 当前能力

当前 MCP 已开放这些工具：

| 工具名 | 说明 |
| --- | --- |
| `validate_login` | 校验当前 Cookie 是否有效，并尝试换取 `accessToken` |
| `refresh_login` | 刷新当前登录态 |
| `get_item_detail` | 获取指定商品详情 |
| `get_item_edit_detail` | 获取指定商品在 PC 编辑页的编辑详情 |
| `list_my_items` | 拉取当前账号名下全部商品列表，并自动翻页聚合 |
| `downshelf_item` | 下架当前账号名下指定商品 |
| `reshelf_item` | 通过 PC 编辑重发布链路重新上架指定商品 |
| `list_conversations` | 拉取最近会话列表 |
| `list_conversation_messages` | 拉取指定会话历史消息 |
| `send_text_message` | 主动发送文本消息 |
| `send_image_message` | 主动发送图片消息 |

当前项目已经验证过这些能力：

- 能读取当前登录用户 `userId`
- 能校验并刷新登录态
- 能拉取当前账号的商品列表
- 能获取商品详情
- 能获取商品编辑详情
- 能执行商品下架
- 能对支持 PC 编辑的商品执行重新上架

## 🚧 当前边界

当前版本优先支持短调用工具，暂未做这些能力的 MCP 化：

- 扫码登录
- 常驻监听消息
- 自动回复 Worker
- 媒体上传独立 MCP 工具
- 新发商品的完整发布链路

底层 `third_party/XianYuApis` 已补充部分商品发布相关原语接口，例如：

- `prepublish_check`
- `preget`
- `edit_item`
- `build_reshelf_payload`

当前 MCP 层只先暴露了更高频、可直接落地的 `get_item_edit_detail` 和 `reshelf_item`。

关于商品上下架，需要额外注意：

- `downshelf_item` 已验证可用于普通商品下架
- `reshelf_item` 本质上走的是 PC 端“编辑并重发布”链路
- 虚拟商品目前会受到闲鱼 PC 端发布管控，调用时可能返回 `FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT`
- 因此当前仓库里，“虚拟商品无法通过 MCP / API 在 PC 端重新上架”属于平台限制，不是仓库参数问题
- 其余支持 PC 编辑的实物商品，当前已验证可以下架、也可以重新上架

如果后续要接 AI 自动客服，建议把“消息监听”和“MCP 短调用”拆成两个进程，不要把常驻循环直接塞进 MCP 主进程。

## 🗂️ 目录结构

```text
xianyu-mcp-server/
├── .mcp/
│   └── XianYuApis_MCP/
│       ├── .env.example
│       ├── README.md
│       ├── pyproject.toml
│       ├── server.py
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

## ⚙️ 快速开始

### 1. 拉取子模块

```bash
git submodule update --init --recursive
```

### 2. 准备环境变量

```bash
cd .mcp/XianYuApis_MCP
cp .env.example .env
```

填写登录态：

```env
XIANYU_COOKIE=你的完整闲鱼 Cookie
```

也支持改为文件方式：

```env
XIANYU_COOKIE_FILE=./cookie.txt
```

`XIANYU_COOKIE` 与 `XIANYU_COOKIE_FILE` 二选一即可。

### 3. 安装依赖

```bash
uv sync --directory .mcp/XianYuApis_MCP
```

### 4. 本地启动 MCP

默认使用 `stdio`：

```bash
uv run --directory .mcp/XianYuApis_MCP server.py
```

如需 HTTP 模式：

```bash
uv run --directory .mcp/XianYuApis_MCP server.py --http
```

HTTP 模式默认监听：`http://localhost:8000/mcp`

## 🔌 Trae 接入

在项目根目录创建或修改 `.trae/mcp.json`：

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

说明：

- `xianyuapis` 只是 MCP 服务名，可以自定义
- 如果你的 Trae 使用的是绝对路径版 `uv`，保留 Trae 自动生成的路径即可
- 配置完成后，重载 Trae 或重新打开工作区

## 🧪 推荐验证流程

接入完成后，建议按这个顺序验证：

1. 调用 `validate_login`，确认当前 Cookie 有效
2. 调用 `list_my_items`，确认能拉到自己的商品列表
3. 调用 `get_item_detail`，确认详情接口可用
4. 如需店铺运维动作，再调用 `downshelf_item`
5. 如需把已下架商品重新挂回去，再调用 `reshelf_item`

## 💡 使用建议

- `list_my_items` 的 `page_size` 推荐使用默认值 `20`
- 某些账号或场景下，服务端会对单页条数做更严格限制，传过大可能返回 `FAIL_BIZ_FORBIDDEN`
- `server.py` 会在每次工具调用时重新读取 `.env`；如果 MCP 客户端自身缓存了进程或配置，更新 Cookie 后仍建议顺手重载一次 MCP 服务

## ❓ 常见问题

### 1. Trae 检测不到闲鱼 MCP

通常是以下原因之一：

- 项目根目录没有 `.trae/mcp.json`
- `mcpServers` 中没有注册当前服务
- `command` 或 `args` 路径写错

### 2. `validate_login` 返回 `FAIL_SYS_USER_VALIDATE`

通常表示当前 Cookie 已失效、不完整，或复制时缺少关键字段。  
请重新从已登录浏览器中复制完整 Cookie，并更新 `.mcp/XianYuApis_MCP/.env`。

### 3. 修改 Cookie 后为什么没有生效

当前实现会在每次工具调用前重新读取 `.env`。通常只要改的是：

- `.mcp/XianYuApis_MCP/.env`
- 或 `XIANYU_COOKIE_FILE` 指向的实际文件

下一次调用通常就会自动读取新值。  
如果当前 MCP 客户端对服务进程做了缓存，重载客户端中的 MCP 服务会更稳妥。

### 4. `list_my_items` 报页数或每页条数超限

请把 `page_size` 调回默认值 `20`。  
虽然工具层做了 `1 ~ 50` 的参数约束，但服务端对不同账号的实际限制可能更严格。

### 5. 为什么仓库里有接口，但 MCP 没有对应工具

`third_party/XianYuApis` 是底层能力库，`.mcp/XianYuApis_MCP` 只封装了其中一部分高频场景。  
当前并不是“底层所有 API 都自动暴露到 MCP”。例如 `prepublish_check`、`preget`、`edit_item` 等目前仍保留为底层调用能力。

### 6. 为什么有些商品能重上架，有些不行

当前 `reshelf_item` 走的是闲鱼 PC 端编辑重发布链路。  
如果商品本身被平台限制为“仅支持 App 发布/编辑”，接口会返回：

- `FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT`

目前实测结论是：

- 虚拟商品通常会命中这类 PC 端管控，无法通过当前 MCP 重新上架
- 支持 PC 编辑的实物商品，可以继续使用 `downshelf_item` / `reshelf_item`

## 📚 相关文档

- MCP 封装说明：[`./.mcp/XianYuApis_MCP/README.md`](./.mcp/XianYuApis_MCP/README.md)
- 底层项目说明：[`./third_party/XianYuApis/README.md`](./third_party/XianYuApis/README.md)
- 商品列表接口记录：[`./third_party/XianYuApis/docs/mtop_idle_web_xyh_item_list.md`](./third_party/XianYuApis/docs/mtop_idle_web_xyh_item_list.md)
- 商品下架接口记录：[`./third_party/XianYuApis/docs/mtop_taobao_idle_item_downshelf.md`](./third_party/XianYuApis/docs/mtop_taobao_idle_item_downshelf.md)
- 商品编辑详情接口记录：[`./third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit_detail.md`](./third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit_detail.md)
- 商品重发布接口记录：[`./third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit.md`](./third_party/XianYuApis/docs/mtop_idle_pc_idleitem_edit.md)
