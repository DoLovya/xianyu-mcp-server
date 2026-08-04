## Context

当前 `xianyu-mcp` 在运行时通过 `third_party/pyxianyu` 目录做动态导入（`sys.path.insert` + `os.chdir`），因此必须先 clone 仓库并初始化 submodule 才能启动。该模式无法满足 “安装即用”（PyPI/uvx）场景：安装后的 wheel 不包含 submodule 目录结构，且 `chdir` 会对服务进程产生全局副作用。

方案 A 的前置条件是：`pyxianyu` 以独立分发包形式提供稳定的 `pyxianyu.*` 命名空间（`pyxianyu.apis/core/utils/message/...`），并由 `xianyu-mcp` 显式依赖它。

## Goals / Non-Goals

**Goals:**
- `xianyu-mcp` 在仅 `pip/uv/uvx install xianyu-mcp` 的情况下可启动（不要求源码 checkout / submodule）
- 运行时导入路径以 `pyxianyu.*` 为唯一必选依赖
- 仓库开发态可选支持从本地 `third_party/pyxianyu` 使用最新代码（fallback），但不影响安装态

**Non-Goals:**
- 在本变更内完成 `pyxianyu` 的打包改造与发布（由 `pyxianyu-pypi-package` 变更负责）
- 调整 MCP 工具能力、协议、请求参数与返回结构
- 一次性清理所有 `xianyu-mcp` 对 `pyxianyu` 的重复依赖（可在稳定后做瘦身）

## Decisions

1) **导入策略：默认使用已安装包**
- 直接导入 `pyxianyu` 命名空间：
  - `from pyxianyu import apis, core, goofish_live, message`
  - `from pyxianyu.utils import goofish_utils`
- 不再依赖 `os.chdir`，避免影响进程内其它逻辑（尤其是 WebSocket/文件读写/日志路径等潜在副作用）。

2) **开发态 fallback：仅在 ImportError 且本地 submodule 存在时启用**
- 当 `import pyxianyu` 失败，且检测到仓库内 `third_party/pyxianyu/src` 存在时，将该路径临时插入 `sys.path` 后再次尝试导入。
- fallback 仅作为开发便利；发布包运行不需要该目录存在。

3) **依赖声明：显式依赖 `pyxianyu`**
- 在 `pyproject.toml` 的 `dependencies` 中增加 `pyxianyu>=<min_version>`（版本下限与 `pyxianyu` 首个发布版本对齐）。
- 初期允许保留当前 `xianyu-mcp` 中的依赖项以降低发布风险；待 `pyxianyu` 的依赖稳定后再做去重。

## Risks / Trade-offs

- 版本错配：`pyxianyu` API/模块路径变更导致 `xianyu-mcp` 启动失败 → 通过最小版本约束 + 在 CI 增加“安装态 smoke import”缓解
- fallback 掩盖发布问题：开发环境因为 submodule 存在导致误以为发布包可用 → 通过在 CI 中显式模拟“无 submodule”环境验证缓解
- 启动时导入成本：导入链路从动态导入转为常规 import，整体更可预测，但需要保证 `pyxianyu` 包内部导入开销可接受 → 通过 compileall/smoke test 观察

