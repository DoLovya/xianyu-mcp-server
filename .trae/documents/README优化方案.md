# README.md 优化方案

## 概述

通过对 `README.md` 与实际代码库的逐项对比，发现当前文档存在 **6 处事实性路径错误、1 处仓库引用错误、1 个工具遗漏、3 处内容重复、4 处 heading-echo、13 个 emoji 标题** 等问题。优化后预计从 389 行压缩至约 280-310 行，消除全部事实性错误。

## 现状分析

### 事实性错误验证

| 验证项 | README 声称 | 实际情况 | 验证来源 |
|--------|------------|---------|---------|
| 子模块路径 | `third_party/XianYuApis` | `third_party/pyxianyu` | `.gitmodules` 第 1-3 行 |
| 子模块来源 | `cv-cat/XianYuApis` | `DoLovya/pyxianyu` | `.gitmodules` url 字段 |
| 工具数量 | 11 个 | 12 个 | `server.py` 第 118-133 行注册了 `publish_physical_item` |
| 代码路径常量 | 未提及 | `xianyu_api_tools.py` 第 17 行确认 `third_party/pyxianyu` | 源码 |
| MCP 封装路径 | `.mcp/XianYuApis_MCP` | `src/xianyu_mcp/` | 实际目录结构 |

### 文档质量问题汇总

- **P0 事实性错误**：6 处路径 + 1 处仓库引用 + 1 处不存在的路径
- **P1 内容过时**：工具表缺 1 项、已知限制描述过时、底层接口列表不完整
- **P2 内容重复**：3 处违反 one-statement rule（虚拟商品限制、Cookie 说明、已验证能力列表）
- **P3 格式问题**：13 个 emoji 标题、4 处 heading-echo、无目录、客户端接入章节冗长（占全文 35%）

## 修改方案

### P0：事实性错误（必须修复）

#### 1. 全文替换子模块路径 `XianYuApis` → `pyxianyu`

涉及 6 处：

| 位置 | 当前内容 | 修改为 |
|------|---------|--------|
| 第 3 行 | `基于 \`third_party/XianYuApis\` 封装` | `基于 \`third_party/pyxianyu\` 封装` |
| 第 15 行 | `- \`third_party/XianYuApis\`：闲鱼底层` | `- \`third_party/pyxianyu\`：闲鱼底层` |
| 第 38 行 | `│   └── XianYuApis/` | `│   └── pyxianyu/` |
| 第 85 行 | `底层 \`third_party/XianYuApis\` 已补充` | `底层 \`third_party/pyxianyu\` 已补充` |
| 第 355 行 | `\`third_party/XianYuApis\` 是底层能力库` | `\`third_party/pyxianyu\` 是底层能力库` |
| 第 372-378 行 | 7 条 `./third_party/XianYuApis/...` 链接 | 全部替换为 `./third_party/pyxianyu/...` |

已验证 7 个文档文件在 `third_party/pyxianyu/docs/` 下全部存在。

#### 2. 修正鸣谢部分的仓库引用

当前第 5-9 行引用 `cv-cat/XianYuApis`，但实际子模块来自 `DoLovya/pyxianyu`。`cv-cat/XianYuApis` 是 pyxianyu 的上游项目。

修改为：

```markdown
## 鸣谢

- https://github.com/DoLovya/pyxianyu （当前子模块来源）
- https://github.com/cv-cat/XianYuApis （pyxianyu 上游项目）
- https://github.com/shaxiu/XianyuAutoAgent
- https://github.com/zhinianboke/xianyu-auto-reply
```

#### 3. 修正项目概览中的不存在路径

当前第 16 行 `- \`.mcp/XianYuApis_MCP\`：面向 MCP 的工具封装`，该路径不存在。

修改为：

```markdown
仓库分两层：

- `third_party/pyxianyu`：闲鱼底层 HTTP / WebSocket 能力（git submodule）
- `src/xianyu_mcp/`：面向 MCP 的工具封装
```

### P1：内容过时与不完整

#### 4. 工具表补充 `publish_physical_item`

在工具表中 `reshelf_item` 行之后插入：

```markdown
| `publish_physical_item` | 在闲鱼 PC 端发布全新实体商品，支持自动上传图片 |
```

#### 5. 删除"已验证能力"列表

第 65-73 行的 7 条已验证能力与工具表高度重叠，违反 one-statement rule。整段删除，在工具表上方加一句：

```markdown
以下工具均已在实际闲鱼账号上验证可用：
```

#### 6. 更新"已知限制"中的发布链路描述

当前问题：
- "新发商品的完整发布链路"已通过 `publish_physical_item` 实现，不应再列入"暂未做"
- 底层接口列表遗漏了 `publish_item`
- "当前 MCP 层只先暴露了 `get_item_edit_detail` 和 `reshelf_item`" 不准确

修改为：

```markdown
以下能力尚未做 MCP 化：

- 扫码登录
- 常驻监听消息
- 自动回复 Worker
- 媒体上传独立 MCP 工具

底层 `third_party/pyxianyu` 的 `ItemApi` 已实现完整的商品发布原语链路：

- `prepublish_check`：发布前校验
- `preget`：获取发布/编辑所需预置参数
- `edit_item`：PC 编辑接口提交
- `build_reshelf_payload`：基于编辑详情构造重发布 payload
- `publish_item`：直接发布全新商品

MCP 层已从中封装出 `get_item_edit_detail`、`reshelf_item`、`publish_physical_item` 三个工具。`prepublish_check`、`preget` 等原语仍保留为底层调用能力，未单独暴露。
```

#### 7. FAQ #5 同步更新

将路径 `XianYuApis` 改为 `pyxianyu`，并补充 `publish_item` 到底层接口说明中。

### P2：内容去重

#### 8. 重写项目结构树

当前结构树缺少 `openspec/`、`LICENSE`、`.gitmodules`，`.trae/` 只展示 `mcp.json`，子模块名错误。重写为：

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
│   └── pyxianyu/                  # 闲鱼底层 HTTP/WebSocket 能力（git submodule）
│       ├── apis/                  # auth_api, item_api, media_api
│       ├── core/                  # client, exceptions
│       ├── docs/                  # 接口分析文档
│       ├── message/               # 消息类型定义
│       ├── utils/                 # 签名、Cookie 处理
│       ├── goofish_live.py        # WebSocket 消息收发
│       └── goofish_apis.py        # HTTP API 封装
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

#### 9. 消除虚拟商品限制的重复

虚拟商品限制在"已知限制"（第 94-100 行）和 FAQ #6（第 358-368 行）重复。保留 FAQ #6 作为唯一规范位置，"已知限制"中压缩为一行引用：

```markdown
- 虚拟商品受闲鱼 PC 端发布管控，无法通过当前 MCP 重新上架（详见常见问题）
```

#### 10. 消除 Cookie 说明的重复

Cookie 更新机制在"快速开始"、"使用建议"、FAQ #3 三处重复。保留 FAQ #3 为唯一解释位置，"使用建议"中删除重复行。

### P3：结构与格式优化

#### 11. 去除所有标题 emoji

13 个标题全部去掉 emoji 前缀，如 `## 🚀 功能特性` → `## 功能特性`。

#### 12. 添加目录

在标题和简介之间插入 TOC，锚点匹配去 emoji 后的标题。

#### 13. 精简客户端接入章节

当前 5 个客户端各独立展示完整 JSON 配置（136 行，占全文 35%），改为"通用配置 + 差异表"结构，预计压缩至约 30 行：

```markdown
## 客户端接入

本项目基于标准 MCP 协议，支持任何兼容 MCP 的客户端。除 Cherry Studio 外均使用 `stdio` 传输模式。

通用配置（以 Trae 为例）：

```json
{
  "mcpServers": {
    "xianyuapis": {
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "xianyu-mcp"]
    }
  }
}
```

各客户端差异：

| 客户端 | 配置文件路径 | 支持 `${workspaceFolder}` | 备注 |
|--------|-------------|--------------------------|------|
| Trae | `.trae/mcp.json` | 是 | 配置后重载工作区 |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS） | 否，需绝对路径 | 保存后重启 |
| Cursor | `.cursor/mcp.json`（项目级）或 `~/.cursor/mcp.json`（全局） | 项目级支持 | 全局配置需绝对路径 |
| VS Code | `.vscode/mcp.json` | 是 | 使用 `"servers"` 字段，需显式 `"type": "stdio"`；需 VS Code 1.102+ |
| Cherry Studio | UI 配置，无配置文件 | N/A | 设置 → MCP 服务器 → 添加，类型选 STDIO |
```

#### 14. 消除 heading-echo

| 位置 | 当前首句 | 修改方向 |
|------|---------|---------|
| 第 49 行 | `当前 MCP 已开放这些工具：` | 改为"以下工具均已在实际账号上验证可用："或直接展示表格 |
| 第 65 行 | `当前项目已经验证过这些能力：` | 整段删除（见修改点 5） |
| 第 77 行 | `当前版本优先支持短调用工具，暂未做这些能力的 MCP 化：` | 改为"以下能力尚未做 MCP 化：" |
| 第 26 行 | `采用 Python 主流的 src layout，仅展示主要文件。` | 直接展示结构树 |

#### 15. 补充徽章

在标题下方添加版本、协议、Python 版本徽章：

```markdown
# xianyu-mcp-server

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3.0-green)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](./pyproject.toml)
```

版本号 `0.1.0` 来自 `pyproject.toml` 第 3 行，Python `>=3.11` 来自第 5 行。

## 假设与决策

1. **emoji 取舍**：根据 doc-writing-guide 技能约束去除 emoji。如果用户倾向保留 emoji 风格，此项可回退
2. **"使用建议"章节**：内容去重后仅剩 1 条，考虑合并入"推荐验证流程"或"常见问题"，而非单独成章
3. **客户端接入精简**：使用差异表替代重复的 JSON 配置块。如果用户认为新手需要完整示例，可保留 1-2 个完整配置作为参考

## 附带发现（README 之外）

以下文件也存在同样的 `XianYuApis` → `pyxianyu` 命名不一致问题，建议一并修复：

- `pyproject.toml` 第 4 行 `description = "基于 XianYuApis 的闲鱼 MCP 服务"`
- `server.py` 第 38 行 instructions 字符串中 `"基于 XianYuApis 的闲鱼 MCP 服务。"`

## 验证步骤

1. 全文搜索 `XianYuApis`，确认无残留（`third_party/pyxianyu` 内部文件除外）
2. 确认工具表共 12 行，与 `server.py` 中 `@mcp.tool()` 注册数一致
3. 点击"相关文档"中的 7 条链接，确认路径可正确跳转
4. 确认结构树中列出的文件/目录在仓库中实际存在
5. 确认无 heading-echo（每个章节首句不复述标题）
6. 确认无内容重复（同一结论只在一个规范位置出现）
