# xianyu-mcp-server

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![CI](https://github.com/DoLovya/xianyu-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/DoLovya/xianyu-mcp-server/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-GPL%20v3.0-green)](./LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](./pyproject.toml)

基于 `pyxianyu` 封装的闲鱼 MCP 项目，用于把闲鱼商品、会话、消息发送等能力接入支持 MCP 的客户端。

> **风险提示**：本项目仅供学习与技术研究使用。通过自动化手段操作闲鱼账号存在被平台风控、限制功能甚至封号的风险，使用者需自行承担一切后果。详见[免责声明](#免责声明)。

## 目录

- [鸣谢](#鸣谢)
- [项目概览](#项目概览)
- [项目结构](#项目结构)
- [功能特性](#功能特性)
- [已知限制](#已知限制)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [客户端接入](#客户端接入)
- [推荐验证流程](#推荐验证流程)
- [常见问题](#常见问题)
- [相关文档](#相关文档)
- [使用协议](#使用协议)
- [免责声明](#免责声明)
- [贡献指南](./CONTRIBUTING.md)

## 鸣谢

- https://github.com/cv-cat/XianYuApis
- https://github.com/shaxiu/XianyuAutoAgent
- https://github.com/zhinianboke/xianyu-auto-reply

## 项目概览

仓库分两层：

- `pyxianyu`：闲鱼底层 HTTP / WebSocket 能力（推荐通过 PyPI 安装；仓库内 submodule 仅用于开发调试）
- `src/xianyu_mcp/`：面向 MCP 的工具封装

适合的使用场景：

- 在 Trae、Cherry Studio、Claude Desktop 等支持 MCP 的客户端中直接调用闲鱼能力
- 把闲鱼卖家工作流接入自定义 Agent / 工作流编排系统
- 作为后续自动客服、消息分发、店铺运维脚本的基础设施

## 项目结构

```text
xianyu-mcp-server/
├── src/
│   └── xianyu_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP 工具注册与入口
│       └── tools/
│           ├── __init__.py
│           └── xianyu_api_tools.py # 底层能力封装
├── third_party/
│   └── pyxianyu/                  # 可选：pyxianyu 源码（git submodule，仅开发调试）
│       ├── src/pyxianyu/apis/     # auth_api, item_api, media_api
│       ├── src/pyxianyu/core/     # client, exceptions
│       ├── docs/                  # 接口分析文档
│       ├── src/pyxianyu/message/  # 消息类型定义
│       ├── src/pyxianyu/utils/    # 签名、Cookie 处理
│       ├── src/pyxianyu/xianyu_live.py # WebSocket 消息收发
│       └── src/pyxianyu/xianyu_apis.py # HTTP API 封装
├── openspec/
│   └── changes/                   # 规范驱动的变更记录
├── .trae/
│   ├── commands/                  # OPSX 工作流命令
│   ├── skills/                    # OpenSpec 技能定义
│   ├── specs/                     # 规范归档
│   └── mcp.json                   # Trae MCP 配置
├── .env.example
├── .gitmodules
├── LICENSE
├── pyproject.toml
├── uv.lock
└── README.md
```

## 功能特性

当前 MCP 已开放这些工具：

| 工具名                       | 说明                                                                |
| ---------------------------- | ------------------------------------------------------------------- |
| `validate_login`             | 校验当前 Cookie 是否有效，并尝试换取 `accessToken`                  |
| `refresh_login`              | 刷新当前登录态                                                      |
| `get_my_profile`             | 获取当前登录用户个人信息（个人页导航数据）                          |
| `search_items`               | 按关键词搜索闲鱼商品（支持分页与排序）                              |
| `get_item_detail`            | 获取指定商品详情                                                    |
| `get_item_edit_detail`       | 获取指定商品在 PC 编辑页的编辑详情                                  |
| `list_my_items`              | 拉取当前账号名下全部商品列表，并自动翻页聚合                        |
| `downshelf_item`             | 下架当前账号名下指定商品                                            |
| `reshelf_item`               | 通过 PC 编辑重发布链路重新上架指定商品                              |
| `edit_item`                  | 编辑指定商品信息（仅支持 PC 可编辑的实体商品）                      |
| `publish_physical_item`      | 在闲鱼 PC 端发布全新实体商品，支持自动上传图片                      |
| `upload_media`               | 上传本地文件或 URL 素材，返回可复用的媒体 URL                       |
| `list_conversations`         | 拉取最近会话列表                                                    |
| `list_conversation_messages` | 拉取指定会话历史消息                                                |
| `send_text_message`          | 主动发送文本消息                                                    |
| `send_image_message`         | 主动发送图片消息                                                    |
| `qr_login_generate`          | 生成扫码登录二维码（返回 session_id 与 base64 data-url）            |
| `qr_login_status`            | 查询扫码登录会话状态（含人脸验证二维码 data-url）                   |
| `qr_login_cookie`            | 在扫码登录成功后获取完整 Cookie（已尽量补齐 `_m_h5_tk` 等关键字段） |
| `qr_login_save_env`          | 显式将 `qr_login_cookie` 的结果写入 `.env`（无需手动复制）          |

### 用户信息相关用法

- 获取当前账号的个人信息（昵称/头像/地区等以接口返回为准）：调用 `get_my_profile`，结果同时包含结构化 `profile` 与原始响应 `raw`（便于你自定义字段映射）。

### 多媒体相关用法

- 直接上传素材拿到可复用 URL：调用 `upload_media`，将返回的 `url` 保存起来，用于后续构造 `edit_item` payload 或消息内容。
- 发布商品图：优先直接用 `publish_physical_item(images=[...])`，内部会自动上传并构造 `imageInfoDOList`。
- 发送图片消息：调用 `send_image_message(image=...)`，支持本地绝对路径或 http/https URL。

## 已知限制

以下能力尚未做 MCP 化：

- 常驻监听消息
- 自动回复 Worker
- 语音/视频消息发送工具

底层 `third_party/pyxianyu` 的 `ItemApi` 已实现完整的商品发布原语链路：

- `prepublish_check`：发布前校验
- `preget`：获取发布/编辑所需预置参数
- `edit_item`：PC 编辑接口提交
- `build_reshelf_payload`：基于编辑详情构造重发布 payload
- `publish_item`：直接发布全新商品

MCP 层已从中封装出 `get_item_edit_detail`、`reshelf_item`、`edit_item`、`publish_physical_item` 等工具。`prepublish_check`、`preget` 等原语仍保留为底层调用能力，未单独暴露。

关于商品上下架，需要额外注意：

- `downshelf_item` 已验证可用于普通商品下架
- `reshelf_item` 本质上走的是 PC 端"编辑并重发布"链路
- 虚拟商品受闲鱼 PC 端发布管控，无法通过当前 MCP 重新上架（详见常见问题）
- 其余支持 PC 编辑的实物商品，当前已验证可以下架、也可以重新上架

如果后续要接 AI 自动客服，建议把"消息监听"和"MCP 短调用"拆成两个进程，不要把常驻循环直接塞进 MCP 主进程。

## 环境要求

- Python 3.11+
- `uv`（或使用 `pip` 替代，见常见问题）
- 闲鱼登录后的完整 Cookie（可手动抓取，或先启动 MCP 后使用 `qr_login_*` 工具扫码获取）

`uv` 安装方式：

**Windows（PowerShell，推荐）**：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后**关闭并重新打开终端**（或刷新 PATH），然后验证：

```powershell
uv --version
```

**macOS / Linux**：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**跨平台通用（不推荐，可能与系统 Python 冲突）**：

```bash
pipx install uv
# 或
pip install --user uv
```

## 快速开始

### 1. 克隆仓库并拉取子模块

```bash
git clone https://github.com/DoLovya/xianyu-mcp-server.git
cd xianyu-mcp-server
git submodule update --init --recursive
```

### 2. 准备环境变量

```bash
cp .env.example .env
```

在 `.env` 中填写登录态（二选一即可）：

```ini
# 方式一：直接写入完整 Cookie
XIANYU_COOKIE=你的完整闲鱼 Cookie

# 方式二：Cookie 存放在单独文件中
XIANYU_COOKIE_FILE=./cookie.txt
```

优先级：

- 配置了 `XIANYU_COOKIE` 时，`XIANYU_COOKIE_FILE` 会被忽略
- `XIANYU_COOKIE_FILE` 支持相对路径（相对仓库根目录）和绝对路径

如果你暂时没有 Cookie：

- 先保持 `.env` 为空启动 MCP
- 启动后服务会自动进入“首次配置模式”，在本机打开一个网页展示二维码（`127.0.0.1`），扫码成功后会自动把 Cookie 写回 `.env`
- 调用 `qr_login_generate` 获取二维码并用手机闲鱼/淘宝扫码确认
- 持续调用 `qr_login_status` 直到 `status=success`（如遇风控可能进入 `verification_required`，按提示完成一次验证）
- 调用 `qr_login_cookie` 获取 Cookie
- 可选：调用 `qr_login_save_env` 将 Cookie 写入仓库根目录 `.env`（避免手动复制；写入后通常无需重启，下一次工具调用会自动读取新值）

首次配置模式相关开关（可选）：

```ini
XIANYU_SETUP_ENABLED=1        # 0 表示禁用首次配置模式
XIANYU_SETUP_AUTOSTART=1      # 0 表示启动时不自动弹出（但工具调用仍会返回 requires_login 引导）
XIANYU_SETUP_AUTO_OPEN=1      # 0 表示不自动打开浏览器/验证链接
XIANYU_SETUP_AUTO_WRITE_ENV=1 # 0 表示不自动写入 .env，需要你手动调用 qr_login_save_env
```

### 3. 安装依赖

**使用 uv（推荐）**：

```bash
uv pip install -e third_party/pyxianyu
uv pip install -e .
```

**使用 pip（替代方案，适合装不上 uv 的场景）**：

```bash
pip install -e third_party/pyxianyu
pip install -e .
```

### 4. 本地启动 MCP

默认使用 `stdio`：

```bash
# 推荐（需要 uv）
uv run xianyu-mcp

# 或使用 pip 方案：
python -m xianyu_mcp.server
```

如需 HTTP 模式：

```bash
# 推荐（需要 uv）
uv run xianyu-mcp --http

# 或使用 pip 方案：
python -m xianyu_mcp.server --http
```

HTTP 模式默认监听：`http://localhost:8000/mcp`

> **ℹ️ 安装说明**：本项目 1.0.0 起已支持通过 PyPI 安装（包名 `xianyu-mcp`）。  
> > - 若环境干净且已完成 PyPI 发布：可直接 `pip install xianyu-mcp` 或 `uvx --from xianyu-mcp xianyu-mcp --help` 使用。  
> > - 若从源码开发/首次发布前：**请先 clone 仓库后使用 `uv run` 或 `python -m` 方式运行**，避免 `uvx` 拉到同名第三方旧包导致 `AttributeError` 一类错误。

## 客户端接入

本项目基于标准 MCP 协议，支持任何兼容 MCP 的客户端。除 Cherry Studio 外均使用 `stdio` 传输模式。

> 前置条件：已 clone 仓库并完成依赖安装（见[快速开始](#快速开始)）。

Trae 项目级配置（推荐，已内置在仓库 `.trae/mcp.json`）：

```json
{
  "mcpServers": {
    "xianyu-mcp-server": {
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "xianyu-mcp"],
      "env": {
        "XIANYU_COOKIE": "",
        "XIANYU_COOKIE_FILE": ""
      }
    }
  }
}
```

Trae 会基于 `env` 中出现的键渲染输入框。推荐优先使用 `XIANYU_COOKIE_FILE` 指向一个被 `.gitignore` 忽略的文件路径（例如 `artifacts/xianyu_cookie.txt`），避免把 Cookie 写进配置文件并误提交到仓库。

不支持 `${workspaceFolder}` 的客户端（如 Claude Desktop 全局配置），请使用绝对路径：

```json
{
  "mcpServers": {
    "xianyu-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\<user>\\Code\\xianyu-mcp-server",
        "run",
        "xianyu-mcp"
      ],
      "env": {
        "XIANYU_COOKIE_FILE": "C:\\Users\\<user>\\Code\\xianyu-mcp-server\\artifacts\\xianyu_cookie.txt"
      }
    }
  }
}
```

**装不上 uv 的替代方案（使用 python）**：

```json
{
  "mcpServers": {
    "xianyu-mcp-server": {
      "command": "python",
      "args": ["-m", "xianyu_mcp.server"],
      "cwd": "C:\\Users\\<user>\\Code\\xianyu-mcp-server",
      "env": {
        "XIANYU_COOKIE_FILE": "C:\\Users\\<user>\\Code\\xianyu-mcp-server\\artifacts\\xianyu_cookie.txt"
      }
    }
  }
}
```

Trae 项目级配置也可用 `cwd` 写法（推荐 `cwd` + `${workspaceFolder}` 代替 python args 里的长路径）：

```json
{
  "command": "python",
  "args": ["-m", "xianyu_mcp.server"],
  "cwd": "${workspaceFolder}"
}
```

注意：如果你的 Trae 版本不允许自动修改 `.trae/mcp.json`，请手动把上面 `env` 片段补到你的 `.trae/mcp.json` 对应 server 配置里，然后重载工作区即可看到输入框。

各客户端差异：

| 客户端         | 配置文件路径                                                               | 支持 `${workspaceFolder}` | 备注                                                                                                                                                                                                                                                 |
| -------------- | -------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Trae           | `.trae/mcp.json`                                                           | 是                        | 配置后重载工作区                                                                                                                                                                                                                                     |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS） | 否，需绝对路径            | 保存后重启                                                                                                                                                                                                                                           |
| Cursor         | `.cursor/mcp.json`（项目级）或 `~/.cursor/mcp.json`（全局）                | 项目级支持                | 全局配置需绝对路径                                                                                                                                                                                                                                   |
| VS Code        | `.vscode/mcp.json`                                                         | 是                        | 使用 `"servers"` 字段（非 `"mcpServers"`），需显式 `"type": "stdio"`；需 VS Code 1.102+                                                                                                                                                              |
| Cherry Studio  | UI 配置，无配置文件                                                        | N/A                       | 设置 → MCP 服务器 → 添加，类型选 STDIO，`command` 填 `uv`，`args` 填 `--directory C:\Users\<user>\Code\xianyu-mcp-server run xianyu-mcp`；装不上 uv 时 `command` 填 `python`，`args` 填 `-m xianyu_mcp.server`，**Working directory** 填仓库绝对路径 |

- `xianyu-mcp-server` 只是 MCP 服务名，可以自定义
- `command` 优先使用 `uv`，可使用绝对路径，例如 `/Users/<user>/.trae/tools/uv/latest/uv`
- 装不上 uv 时，`command` 用 `python` + `args: ["-m", "xianyu_mcp.server"]`，并把 `cwd`（或 Working directory）设置为仓库绝对路径
- Windows 路径使用反斜杠，例如 `C:\\Users\\<user>\\Code\\xianyu-mcp-server`
- **推荐使用 `uv run` 而非 `uvx`**：若已完成 PyPI 官方发布，可使用 `uvx --from xianyu-mcp xianyu-mcp`；否则请优先源码方式，避免 `uvx` 装到同名第三方旧包报错

HTTP 模式（可选）：以 `uv run xianyu-mcp --http`（或 `python -m xianyu_mcp.server --http`）启动后，监听 `http://localhost:8000/mcp`，Cherry Studio 等客户端可选 SSE 或 HTTP 类型接入。

## 推荐验证流程

接入完成后，建议按这个顺序验证：

1. 调用 `validate_login`，确认当前 Cookie 有效
2. 调用 `list_my_items`，确认能拉到自己的商品列表
3. 调用 `get_item_detail`，确认详情接口可用
4. 如需店铺运维动作，再调用 `downshelf_item`
5. 如需把已下架商品重新挂回去，再调用 `reshelf_item`

`list_my_items` 的 `page_size` 推荐使用默认值 `20`。某些账号或场景下，服务端会对单页条数做更严格限制，传过大可能返回 `FAIL_BIZ_FORBIDDEN`。

## 常见问题

### 1. 使用 `uvx xianyu-mcp` 报 `AttributeError: 'Server' object has no attribute 'list_tools'`

这是因为**安装到了非官方的同名第三方旧包**。虽然本项目 1.0.0+ 已支持 PyPI 发布（`xianyu-mcp`），但若官方包尚未在 PyPI 上注册成功，或 `uvx` 解析到了同名旧包，会出现该错误。

**解决方法（推荐，避免踩坑）**：优先使用源码 `uv run` 方式：

```bash
git clone https://github.com/DoLovya/xianyu-mcp-server.git
cd xianyu-mcp-server
git submodule update --init --recursive
uv pip install -e third_party/pyxianyu
uv pip install -e .
uv run xianyu-mcp
```

客户端配置中，`command` 使用 `uv`，`args` 使用 `--directory <仓库绝对路径> run xianyu-mcp`。  
若已确认 PyPI 上官方 `xianyu-mcp` 为 DoLovya 发布：可使用 `uvx --from xianyu-mcp xianyu-mcp` 显式指定官方包来避免误装。

### 2. Windows 报 `'uv' 不是内部或外部命令，也不是可运行的程序或批处理文件`

这是因为你的 Windows 系统**没有安装 uv**，或者安装后没有刷新 PATH 环境变量。

**解决方法 A（推荐，安装 uv）**：

1. 在 PowerShell 中执行安装命令：
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. **关闭并重新打开** PowerShell / 终端窗口（这一步很关键，旧终端不会自动加载新 PATH）
3. 验证是否安装成功：
   ```powershell
   uv --version
   ```
4. 回到仓库目录，按 README 的步骤重新执行 `uv pip install -e ...` 和 `uv run xianyu-mcp`。

> 小提示：如果 Trae / Cherry Studio 等客户端已经打开，安装 uv 后最好也重启一下客户端，让它重新读取系统 PATH。

**解决方法 B（不想装 uv，用 pip 替代）**：

如果你不想安装 uv，可以直接用 Python 自带的 pip：

```powershell
# 在仓库根目录执行：
pip install -e third_party/pyxianyu
pip install -e .

# 启动 MCP（stdio 模式）
python -m xianyu_mcp.server

# 或 HTTP 模式
python -m xianyu_mcp.server --http
```

对应的客户端 MCP 配置也要改成 `python` 方式：

```json
{
  "command": "python",
  "args": ["-m", "xianyu_mcp.server"],
  "cwd": "C:\\Users\\<你的用户名>\\Code\\xianyu-mcp-server"
}
```

Trae 项目级推荐写法（自动适配工作区路径）：

```json
{
  "command": "python",
  "args": ["-m", "xianyu_mcp.server"],
  "cwd": "${workspaceFolder}"
}
```

### 3. Trae 检测不到闲鱼 MCP

通常是以下原因之一：

- 项目根目录没有 `.trae/mcp.json`
- `mcpServers` 中没有注册当前服务
- `command` 或 `args` 路径写错

### 4. `validate_login` 返回 `FAIL_SYS_USER_VALIDATE`

通常表示当前 Cookie 已失效/不完整，或触发了更强风控校验。  
建议优先走 `qr_login_generate/status/cookie` 重新获取；如果扫码后仍缺关键字段（例如 `_m_h5_tk` / `x5sec`）导致验证失败，需要按 `qr_login_status` 提示完成一次验证流程后再重试。

### 5. 修改 Cookie 后未生效

当前实现会在每次工具调用前重新读取 `.env`。通常只要改的是：

- 仓库根目录下的 `.env`
- 或 `XIANYU_COOKIE_FILE` 指向的实际文件

下一次调用通常就会自动读取新值。  
如果当前 MCP 客户端对服务进程做了缓存，重载客户端中的 MCP 服务会更稳妥。

### 6. `list_my_items` 报页数或每页条数超限

请把 `page_size` 调回默认值 `20`。  
虽然工具层做了 `1 ~ 50` 的参数约束，但服务端对不同账号的实际限制可能更严格。

### 7. 仓库里有接口，但 MCP 没有对应工具

`third_party/pyxianyu` 是底层能力库，`src/xianyu_mcp` 只封装了其中一部分高频场景。`prepublish_check`、`preget` 等原语仍保留为底层调用能力，未单独暴露到 MCP。

### 8. 部分商品无法重新上架

如果商品本身被平台限制为"仅支持 App 发布/编辑"，接口会返回：

- `FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT`

目前实测结论是：

- 虚拟商品通常会命中这类 PC 端管控，无法通过当前 MCP 重新上架
- 支持 PC 编辑的实物商品，可以继续使用 `downshelf_item` / `reshelf_item`

## 相关文档

- CI/CD：[`./docs/ci-cd.md`](./docs/ci-cd.md)
- 底层项目说明：[`./third_party/pyxianyu/README.md`](./third_party/pyxianyu/README.md)
- 商品列表接口记录：[`./third_party/pyxianyu/docs/mtop_idle_web_xyh_item_list.md`](./third_party/pyxianyu/docs/mtop_idle_web_xyh_item_list.md)
- 商品下架接口记录：[`./third_party/pyxianyu/docs/mtop_taobao_idle_item_downshelf.md`](./third_party/pyxianyu/docs/mtop_taobao_idle_item_downshelf.md)
- 商品预发布检查接口记录：[`./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_prepublish_check.md`](./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_prepublish_check.md)
- 商品预取发布参数接口记录：[`./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_preget.md`](./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_preget.md)
- 商品编辑详情接口记录：[`./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_edit_detail.md`](./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_edit_detail.md)
- 商品编辑重发布接口记录：[`./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_edit.md`](./third_party/pyxianyu/docs/mtop_idle_pc_idleitem_edit.md)

## 使用协议

本项目采用 `GNU General Public License v3.0` 协议。

- 允许：学习、修改、分发与再发布
- 要求：衍生作品在分发时需继续遵循 GPL v3.0 条款
- 提示：第三方依赖或子模块如有单独协议，以其各自协议为准

详细条款见 [`LICENSE`](./LICENSE)。

欢迎参与贡献，详见 [贡献指南](./CONTRIBUTING.md)。

## 免责声明

本项目仅供学习、技术研究与个人自动化实践使用，不用于任何商业用途。

闲鱼（Goofish）是阿里巴巴集团旗下的二手交易平台，本项目未获得阿里巴巴集团的任何授权或认可。本项目通过逆向分析闲鱼 Web 端接口实现自动化操作，可能违反闲鱼用户协议及相关平台规则。

使用本项目可能导致以下风险，包括但不限于：

- 账号被平台风控系统识别，触发功能限制、临时封禁或永久封号
- 账号内商品、资金、信用等资产受到冻结或扣减
- 因接口变更导致工具失效或数据异常

**项目开发者及贡献者不对任何人因使用本项目而产生的任何直接或间接损失承担责任，包括但不限于账号封禁、数据丢失、财产损失。**

使用本项目即表示你已阅读并理解上述风险，并同意自行承担一切后果。如果所在地区法律禁止此类使用，请立即停止使用并删除本项目。
