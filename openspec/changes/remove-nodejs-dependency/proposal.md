## Why

当前 MCP 服务依赖 Node.js 运行时通过 `execjs` 调用 JS 文件（`goofish_js_*.js`）执行签名生成、ID 生成等操作。这个间接依赖增加了环境配置成本（需额外安装 Node.js）、依赖链风险（`PyExecJS` 兼容性问题），但实际涉及的 5 个 JS 函数中有 4 个可以轻易用 Python 标准库替代，第 5 个（`decrypt`）在 MCP 链路中完全未被使用。

去掉 Node.js 依赖能让 `uv run xianyu-mcp` 真正「零外部运行时」启动，降低新开发者的配置门槛。

## What Changes

- 将 `goofish_utils.py` 中的 4 个 execjs 调用（`generate_sign`、`generate_mid`、`generate_uuid`、`generate_device_id`）替换为纯 Python 实现
- `decrypt` 函数保留 execjs fallback 不动（仅 `goofish_live.py` 使用，不影响 MCP 链路）
- 从 `pyproject.toml` 中移除 `PyExecJS` 依赖
- 更新 `README.md` 环境要求，去掉 `Node.js 18+`
- `.js` 源文件保留不动，`decrypt` 仍可正常运行

## Capabilities

### New Capabilities
- `pure-python-sign`: 纯 Python 实现的签名生成与设备标识生成，覆盖原 JS 的 `generate_sign`、`generate_mid`、`generate_uuid`、`generate_device_id`

### Modified Capabilities
-（无现有 spec 被改变行为）

## Impact

- **受影响的文件**:
  - `third_party/XianYuApis/utils/goofish_utils.py` — 核心修改，4 个函数从 execjs 改为 Python
  - `pyproject.toml` — 移除 `PyExecJS` 依赖
  - `README.md` — 环境要求、快速开始章节
- **不影响的文件**:
  - `third_party/XianYuApis/utils/goofish_utils.py:decrypt()` — 保持 execjs 不变
  - `static/goofish_js_*.js` — 保留，仅 `decrypt` 仍使用
  - `goofish_live.py` — 完全不涉及
  - MCP 暴露的工具接口 — 行为完全不变
- **外部依赖变化**: 移除 `PyExecJS`，减少一个隐式 Node.js 运行时依赖
