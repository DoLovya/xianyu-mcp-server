## Summary

将 `/Users/huan.zhang/Code/xianyu-mcp-server/.logs` 加入仓库忽略规则，并补齐与本项目运行/构建相关的常见本地产物忽略项，避免后续新增日志、缓存、构建目录被误提交。

## Current State Analysis

- 当前仓库根目录存在 `.logs/xianyu_mcp.log`（由 `XIANYU_LOG_TO_FILE=1` 触发写入）。
- 当前 [.gitignore](file:///Users/huan.zhang/Code/xianyu-mcp-server/.gitignore) 仅忽略：
  - Python 编译产物：`*.pyc`、`__pycache__/`
  - `.env`（含 Cookie）
  - `.venv`
  - `.DS_Store`
  - `artifacts/`
  - `scripts/`
- `.logs/` 未被忽略，存在被误提交风险。

## Proposed Changes

### 1) 更新根目录 .gitignore

目标文件：
- [/Users/huan.zhang/Code/xianyu-mcp-server/.gitignore](file:///Users/huan.zhang/Code/xianyu-mcp-server/.gitignore)

新增忽略项（以“尽量不误伤源码”为原则）：

- **日志目录/文件**
  - `/.logs/`：忽略仓库根目录的日志输出目录（本项目默认日志落盘位置）。
  - `*.log`：忽略任意 `.log` 文件（避免未来出现其它日志文件散落到目录中）。
  - `*.log.*`：忽略带滚动后缀的日志（如 `xxx.log.1`、`xxx.log.2026-08-02` 等）。
- **测试/构建运行产物（常见且低风险）**
  - `/.pytest_cache/`
  - `/.coverage`
  - `/htmlcov/`
  - `/dist/`
  - `/build/`
  - `/*.egg-info/`
  - `/.mypy_cache/`
  - `/.ruff_cache/`

说明：
- 使用前导 `/` 的目录（如 `/.logs/`、`/dist/`）仅匹配仓库根目录，避免误伤子模块/第三方目录。
- `*.log`/`*.log.*` 为全局规则，主要用于防止日志文件被意外放置到其它路径。

## Assumptions & Decisions

- `.logs/` 仅作为本地运行日志目录，不需要被版本管理。
- 未来可能引入的日志滚动文件、测试缓存、构建目录不应进入仓库；因此一次性补齐常见忽略项。
- 暂不修改第三方子模块（`third_party/pyxianyu`）内的 `.gitignore`，仅处理仓库根目录规则。

## Verification

- 执行 `git status`（或在 IDE Git 面板查看）：
  - `.logs/xianyu_mcp.log` 不再出现在未跟踪/变更列表中。
- 手动创建/滚动一个示例日志文件（如 `.logs/test.log.1`），确认同样被忽略。

