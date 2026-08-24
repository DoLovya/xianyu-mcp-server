# 贡献指南

感谢你对 xianyu-mcp-server 的关注。本文档描述了参与开发需要了解的约定和流程。

## 协议声明

本项目采用 [GPL v3.0](./LICENSE) 协议。提交代码即表示你同意将贡献以 GPL v3.0 协议授权，衍生作品在分发时需继续遵循该条款。第三方子模块 `third_party/pyxianyu` 以其各自协议为准。

## 开发环境搭建

### 前置要求

- Python 3.11+
- `uv`（包管理器）
- Git（含 submodule 支持）

### 1. Fork 并 Clone 仓库

```bash
git clone --recurse-submodules https://github.com/<your-username>/xianyu-mcp-server.git
cd xianyu-mcp-server
```

如果已经 clone 但未拉取子模块：

```bash
git submodule update --init --recursive
```

### 2. 安装依赖

```bash
uv sync
```

`uv sync` 会根据 `uv.lock` 创建虚拟环境并安装全部依赖，无需手动创建 venv。

### 3. 配置环境变量

```bash
cp .env.example .env
```

在 `.env` 中填写闲鱼登录 Cookie（二选一）：

```ini
# 方式一：直接写入完整 Cookie
XIANYU_COOKIE=你的完整闲鱼 Cookie

# 方式二：Cookie 存放在单独文件中
XIANYU_COOKIE_FILE=./cookie.txt
```

**`.env` 文件包含敏感登录凭据，已在 `.gitignore` 中忽略，绝对不要提交。** 详见[敏感信息处理](#敏感信息处理)。

### 4. 验证环境

```bash
# 启动 MCP 服务（stdio 模式）
uv run xianyu-mcp-server

# HTTP 模式
uv run xianyu-mcp-server --http

# 运行测试
uv run python -m unittest discover tests/ -v
```

## 代码风格

### 推荐工具

当前项目未强制配置 linting/formatting 工具。建议在本地安装 [ruff](https://docs.astral.sh/ruff/) 进行代码检查和格式化：

```bash
uv add --dev ruff
uv run ruff format src/ tests/
uv run ruff check src/ tests/
```

### 规范要点

- 4 空格缩进，行宽 100 字符
- 双引号字符串
- 所有公开函数必须添加 type hints（项目已全面使用）
- 新增工具必须添加 docstring，包含 `Args:` 段落说明每个参数
- 遵循现有的 `from __future__ import annotations` 导入风格
- 使用 PEP 604 联合类型语法（如 `dict[str, Any] | None`）

## Git 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>
```

### Type

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式 |
| `refactor` | 重构（不改变行为） |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖 |
| `openspec` | OpenSpec 变更工件 |

### Scope

| Scope | 对应模块 |
|-------|---------|
| `tools` | `src/xianyu_mcp/tools/` |
| `server` | `src/xianyu_mcp/server.py` |
| `guardrails` | `src/xianyu_mcp/guardrails.py` |
| `deps` | 依赖变更 |
| `submodule` | `third_party/pyxianyu` 相关 |

### 示例

```bash
git commit -m "feat(tools): 新增 send_audio_message 工具

支持发送本地语音文件或 URL 语音，复用 MediaApi 上传链路。
对应 OpenSpec 变更: audio-message-support"

git commit -m "fix(guardrails): WRITE 冷却期内未拦截异步工具

冷却判定漏掉了 async 工具路径，补充 run_write_async 的护栏接入。"
```

## OpenSpec 规范驱动开发

本项目使用 [OpenSpec](https://github.com/openspec-dev/openspec) 管理变更。所有非 trivial 的功能新增或行为变更必须先走 OpenSpec 流程。

### 工作流

```
/opsx:propose  →  /opsx:apply  →  /opsx:sync  →  /opsx:archive
   提出变更        实施变更       同步规格        归档变更
```

每个变更位于 `openspec/changes/<change-name>/`，包含以下工件：

- **`proposal.md`**：变更动机（Why）、变更内容（What）、能力清单（Capabilities）、影响面（Impact）
- **`specs/`**：能力规格（delta spec），描述新增或修改的能力
- **`design.md`**：设计决策（Decisions）、目标与非目标（Goals / Non-Goals）、风险权衡（Risks / Trade-offs）
- **`tasks.md`**：实现任务清单，按阶段分组，每项用 `- [ ]` / `- [x]` 标记状态

变更名使用 kebab-case，例如 `anti-bot-rate-limit`、`publish-physical-item`。

### 参考现有变更

- [`anti-bot-rate-limit`](./openspec/changes/anti-bot-rate-limit/)：请求护栏（限速、抖动、退避、熔断）
- [`publish-physical-item`](./openspec/changes/publish-physical-item/)：发布实体商品工具
- [`openspec/changes/archive/`](./openspec/changes/archive/)：已归档的变更

### 何时需要 OpenSpec

| 场景 | 是否需要 |
|------|---------|
| 新增 MCP 工具 | 是 |
| 修改现有工具行为 | 是 |
| 引入新的护栏策略 | 是 |
| 修改底层子模块接口 | 是 |
| 修复 Bug | 视复杂度而定，简单修复可直接 PR |
| 文档修正 | 否 |
| 代码格式化 | 否 |
| 依赖版本升级 | 视影响面而定 |

## Pull Request 流程

### 1. 创建分支

从 `main` 分支创建特性分支：

```bash
git checkout main
git pull origin main
git checkout -b feat/<change-name>
```

分支命名：`<type>/<change-name>`，例如 `feat/audio-message`、`fix/guardrails-deadlock`。

### 2. 提交前自检

```bash
# 代码格式化（如已安装 ruff）
uv run ruff format src/ tests/
uv run ruff check src/ tests/

# 运行测试
uv run python -m unittest discover tests/ -v

# 检查暂存区是否有敏感文件
git diff --cached --name-only | grep -E "\.env$|cookie" && echo "WARNING: 检测到敏感文件!" || echo "OK"
```

### 3. 创建 PR

PR 标题遵循 Conventional Commits 格式。PR 描述建议包含以下内容：

```markdown
## 变更说明

<!-- 简述这个 PR 做了什么、解决了什么问题 -->

## 关联 OpenSpec 变更

<!-- 如果有对应的 OpenSpec 变更，填写变更名 -->
- Change: `<change-name>`

## 检查清单

- [ ] 代码通过测试
- [ ] 新增工具有 docstring 和 type hints
- [ ] 没有提交 `.env`、Cookie 或其他敏感信息
- [ ] 子模块变更已同步（如有）
- [ ] OpenSpec 工件已更新（如有）
- [ ] README 已更新（如涉及用户可见行为变更）
```

### 4. Review 标准

维护者会关注：

- 是否遵循现有代码模式（特别是 [MCP 工具开发规范](#mcp-工具开发规范)）
- 是否正确接入 `RequestGuardrails` 护栏
- 是否有敏感信息泄漏风险
- OpenSpec 工件是否完整（如适用）
- 子模块变更是否必要且最小化

## 敏感信息处理

### 绝对不能提交的内容

| 内容 | 原因 |
|------|------|
| `.env` 文件 | 包含闲鱼登录 Cookie |
| 硬编码 Cookie 字符串 | 泄漏登录凭据 |
| 完整 `accessToken` | 闲鱼鉴权 token |
| 用户 ID、会话 ID（日志中） | 个人隐私信息 |

`.env.example` 是模板文件，只包含空值占位符，可以提交。**绝对不要在 `.env.example` 中填写真实 Cookie。**

### 代码中的脱敏处理

参考 `src/xianyu_mcp/tools/xianyu_api_tools.py` 中的现有实现：

```python
# 正确：token 预览只显示前 16 位
"access_token_preview": token[:16] + "..." if token else "",

# 正确：错误信息不包含 Cookie 原文
raise ValueError(
    "未配置闲鱼 Cookie。请在 .env 中填写 XIANYU_COOKIE，或提供 XIANYU_COOKIE_FILE。"
)
```

### 不慎泄漏后的处理

1. 立即让该 Cookie 失效（重新登录闲鱼获取新 Cookie）
2. 联系维护者强制删除相关 commit（不要只做新 commit 删除，git 历史仍会保留）
3. 更新本地 `.env` 中的 Cookie

## Git Submodule 管理

### 项目子模块

| 子模块 | 路径 | 上游仓库 |
|--------|------|---------|
| pyxianyu | `third_party/pyxianyu` | https://github.com/DoLovya/pyxianyu.git |

### 不要直接在主仓库中修改子模块代码

`third_party/pyxianyu` 是独立仓库。如果需要修改子模块：

- 去 [pyxianyu 上游仓库](https://github.com/DoLovya/pyxianyu) 提 PR
- 或 Fork 子模块仓库后修改 `.gitmodules` 指向你的 Fork

### 职责边界

- `third_party/pyxianyu`：底层 HTTP/WebSocket 能力（`auth_api`、`item_api`、`media_api`、`client`、`goofish_live`）
- `src/xianyu_mcp/`：MCP 工具封装（`server.py` 注册工具，`tools/xianyu_api_tools.py` 实现逻辑，`guardrails.py` 请求护栏）

新增能力时，底层能力放子模块，MCP 封装放 `src/xianyu_mcp/`。

### 更新子模块

```bash
cd third_party/pyxianyu
git fetch origin
git checkout main
git pull origin main
cd ../../
git add third_party/pyxianyu
git commit -m "chore(submodule): 更新 pyxianyu 到最新版本"
```

## MCP 工具开发规范

### 三层架构

```
server.py (@mcp.tool 装饰器，注册工具)
    ↓
tools/xianyu_api_tools.py (XianYuApiTools 类，业务逻辑)
    ↓
guardrails.py (RequestGuardrails，请求护栏)
    ↓
third_party/pyxianyu (底层 API 调用)
```

### 新增工具的步骤

#### 1. 在 XianYuApiTools 中实现业务逻辑

在 `src/xianyu_mcp/tools/xianyu_api_tools.py` 中添加方法：

```python
def get_item_detail(self, item_id: str) -> str:
    """获取指定闲鱼商品详情。"""
    # READ 操作使用 run_read，WRITE 操作使用 run_write
    result = self._guardrails.run_read(
        lambda: self._get_item_api().get_item_info(item_id)
    )
    return _dump(result)  # 统一使用 _dump 序列化为 JSON 字符串
```

关键规范：

- 所有工具方法返回 `str`（JSON 字符串），使用 `_dump()` 序列化
- READ 操作使用 `self._guardrails.run_read()`，WRITE 操作使用 `self._guardrails.run_write()`
- 异步工具使用 `self._guardrails.run_read_async()` / `run_write_async()`
- 参数校验在方法入口处完成（参考 `list_my_items` 的 `page_size` 限制：`min(max(page_size, 1), 50)`）

#### 2. 在 server.py 中注册工具

在 `src/xianyu_mcp/server.py` 中添加注册：

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))  # READ 工具标记 readOnlyHint
def get_item_detail(item_id: str) -> str:
    """获取指定闲鱼商品详情。

    Args:
        item_id: 商品 ID，例如 1001160709960。
    """
    return _get_tools().get_item_detail(item_id=item_id)
```

关键规范：

- READ 工具添加 `annotations=ToolAnnotations(readOnlyHint=True)`
- WRITE 工具使用 `@mcp.tool()` 不加 `readOnlyHint`（默认为 False）
- 函数签名与 `XianYuApiTools` 中的方法保持一致
- docstring 会暴露给 MCP 客户端，必须清晰描述功能和参数

#### 3. 更新 instructions

新增工具后，更新 `server.py` 中 `FastMCP` 的 `instructions` 字符串，列出所有可用工具。

### 工具分类

| 分类 | 护栏方法 | `readOnlyHint` | 现有工具 |
|------|---------|----------------|---------|
| READ | `run_read()` | `True` | `validate_login`、`get_item_detail`、`get_item_edit_detail`、`list_my_items`、`list_conversations`、`list_conversation_messages` |
| WRITE | `run_write()` | 不设 | `refresh_login`、`downshelf_item`、`reshelf_item`、`edit_item`、`publish_physical_item`、`send_text_message`、`send_image_message` |

### 命名规范

- 工具名使用 `snake_case`，动词在前：`get_`、`list_`、`send_`、`edit_`、`publish_`、`validate_`、`refresh_`、`downshelf_`、`reshelf_`
- 参数名使用 `snake_case`
- 必须添加 type hints
- 可选参数提供默认值

## 测试规范

项目使用 Python 标准库 `unittest`，测试文件位于 `tests/` 目录。

### 文件与命名

- 测试文件：`tests/test_<module>.py`
- 测试类：`Test<ClassName>`（继承 `unittest.TestCase`）
- 测试方法：`test_<scenario>`

### 示例

参考 `tests/test_guardrails.py`，使用 `_FakeClock` 类和 `patch` 隔离外部依赖：

```python
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from xianyu_mcp.guardrails import RequestGuardrails


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += max(0.0, float(seconds))


class TestRequestGuardrails(unittest.TestCase):
    def test_read_min_interval(self) -> None:
        clock = _FakeClock()
        guard = RequestGuardrails()
        # ...
```

### 运行测试

```bash
uv run python -m unittest discover tests/ -v
```
