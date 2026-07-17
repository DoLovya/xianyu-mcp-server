# 更新 third_party/XianYuApis/README.md 规范

## Why

`third_party/XianYuApis/README.md` 中的多处描述与实际代码已不一致：
- Node.js 依赖在 `remove-nodejs-dependency` 变更后已完全移除，但文档仍要求安装 Node 18+
- `static/` 目录已删除，但项目结构图仍包含它
- Cookie 配置指引引导修改 `goofish_live.py` 底部，实际应通过 `.env` 注入
- AI 集成示例仍指向直接修改 `goofish_live.py`，与 MCP Server 使用方式脱节
- 包含上游项目无关的内容（Star 趋势图、赞赏码）

## What Changes

- 移除 Node.js 依赖标识（badge + 环境要求 + npm install）
- 更新安装命令为 `pip install -r requirements.txt`（仅保留 Python 依赖）
- 更新 Cookie 配置指引为 `.env` 方式，而非修改源码
- 更新项目结构图，删除 `static/` 条目
- 更新 AI 集成示例为 MCP Server 的集成方式
- 精简尾部内容：保留授权信息，移除 upstream 特有的 Star 趋势图与赞赏码
- 调整标题与描述，明确此为 vendor 库而非独立项目
- 同步更新 HTTP API 能力表（如有增减）

## Impact

- Affected specs: 无
- Affected code: `third_party/XianYuApis/README.md`
