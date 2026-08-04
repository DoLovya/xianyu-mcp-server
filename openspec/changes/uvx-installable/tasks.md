## 1. Dependencies

- [x] 1.1 在 `pyproject.toml` 增加 `pyxianyu>=<min_version>` 运行时依赖
- [x] 1.2 评估并决定是否移除 `xianyu-mcp` 中已由 `pyxianyu` 提供的重复依赖（可先保留，后续瘦身）

## 2. Runtime Import Refactor

- [x] 2.1 将 `xianyu_api_tools._load_xianyu_modules()` 改为直接导入 `pyxianyu.*`（不再依赖 `third_party/pyxianyu` 目录结构）
- [x] 2.2 增加开发态 fallback：当 `import pyxianyu` 失败且存在 `third_party/pyxianyu/src` 时，临时加入 `sys.path` 后重试导入
- [x] 2.3 调整缺依赖时的报错信息：提示安装 `pyxianyu`（并说明 submodule 仅为开发可选）

## 3. Documentation

- [x] 3.1 更新 README 的安装/接入：提供 `uvx xianyu-mcp` 的推荐用法与 MCP 配置示例（无需 clone）
- [x] 3.2 增补开发说明：源码开发时如何使用本地 `third_party/pyxianyu`（以及与已安装版本的优先级策略）

## 4. Verification

- [x] 4.1 在 CI 增加 “安装态导入” 校验：确保在不含 `third_party/pyxianyu` 的情况下 `python -c "import xianyu_mcp"` 与初始化导入链路均可通过
- [x] 4.2 本地验证 `uvx xianyu-mcp` 启动（至少完成一次启动到服务监听/可响应的 smoke check）
