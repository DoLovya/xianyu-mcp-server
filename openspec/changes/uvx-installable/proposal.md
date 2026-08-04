## Why

当前 `xianyu-mcp` 需要用户 clone 仓库并初始化 submodule 才能启动，接入成本高，不符合“像其它 MCP 一样直接 `uvx` 运行”的使用预期。

将底层依赖 `pyxianyu` 改为 PyPI 可安装包后，`xianyu-mcp` 可以作为纯 Python 包分发，实现开箱即用的 `uvx xianyu-mcp` 启动体验。

## What Changes

- 将 `third_party/pyxianyu` 的运行时依赖替换为 `pip install pyxianyu`（不再依赖本地 submodule 目录结构）
- 调整 `xianyu_mcp` 的底层加载逻辑：优先从 site-packages 导入 `pyxianyu`，开发态可选 fallback 到 submodule
- 更新 README：提供 `uvx` 方式的 MCP 配置示例（无需 clone）

## Capabilities

### New Capabilities
- `uvx-install`: 通过 `uvx` 一条命令安装并运行 `xianyu-mcp`，无需源码 checkout

### Modified Capabilities
- （无）

## Impact

- `src/xianyu_mcp/tools/xianyu_api_tools.py` 的导入路径与模块加载方式会调整
- `pyproject.toml` 依赖将从“隐式依赖 submodule”变为显式依赖 `pyxianyu`
- README 的快速开始与客户端接入章节将更新为“uvx 优先”
