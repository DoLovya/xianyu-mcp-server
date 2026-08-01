## Summary

将 `FirstRunSetup` 的内联 HTML/CSS/JS 从 Python 三引号字符串中拆分为可维护的静态资源文件（不引入 Node/React/Vue/Jinja2），并完善静态资源的打包与回归测试，保持现有 `/status` 轮询与二维码/验证入口逻辑不变。

## Current State Analysis

- 首次配置页面由 [first_run_setup.py](file:///Users/huan.zhang/Code/xianyu-mcp-server/src/xianyu_mcp/first_run_setup.py#L166-L321) 的 `_render_html()` 直接返回长字符串。
- 页面动态数据通过 JS 轮询 `/status`（[first_run_setup.py](file:///Users/huan.zhang/Code/xianyu-mcp-server/src/xianyu_mcp/first_run_setup.py#L252-L318)）。
- 当前工程依赖列表中没有模板引擎（见 [pyproject.toml](file:///Users/huan.zhang/Code/xianyu-mcp-server/pyproject.toml#L1-L19)），且历史上有 “remove-nodejs-dependency” 变更，说明应避免引入 Node 构建链路。
- 现有测试已覆盖 `/status` 端点与 requires_login 响应（见 [test_first_run_setup.py](file:///Users/huan.zhang/Code/xianyu-mcp-server/tests/test_first_run_setup.py)），但未覆盖 “主页 HTML 可正常返回且结构符合预期”。

## Proposed Changes

### 1) 拆分静态资源（HTML/CSS/JS）

**目标：** 不改变页面能力，只提升可维护性与可读性。

- 新增目录：`src/xianyu_mcp/static/first_run_setup/`
  - `index.html`：页面骨架（包含最少的内联脚本；或拆成 `app.js` 亦可）
  - （可选）`app.js`：轮询 `/status` + DOM 更新逻辑
  - （可选）`style.css`：样式
- 页面仍通过 `fetch("/status")` 获取数据，不引入任何构建步骤。

### 2) 服务端从静态文件加载页面

- 修改 [FirstRunSetup._render_html](file:///Users/huan.zhang/Code/xianyu-mcp-server/src/xianyu_mcp/first_run_setup.py#L166)：
  - 改为读取 `importlib.resources` 中的 `index.html` 内容并返回
  - 对读取失败返回一个极简 fallback HTML（避免服务崩溃），并在页面上提示 error_message
- 如需支持 css/js 文件：
  - 在 `Handler.do_GET` 增加静态文件路由（例如 `/static/...`），只允许读取 `first_run_setup/` 子目录下的资源
  - 正确设置 `Content-Type`（html/css/js/png 等）

### 3) 让静态资源进入打包产物

当前 wheel 配置为 `packages = ["src/xianyu_mcp"]`（见 [pyproject.toml](file:///Users/huan.zhang/Code/xianyu-mcp-server/pyproject.toml#L24-L25)），需要显式把 `static/**` 包含进 wheel。

- 增加 hatchling 打包配置（示例方案）：
  - 在 `pyproject.toml` 增加 `tool.hatch.build.targets.wheel.include = ["src/xianyu_mcp/static/**"]`
- 验证：`uv build` 产物中包含静态文件（在实现阶段通过命令校验）

### 4) 回归测试补齐

- 新增单测：请求首次配置页 `/`，断言：
  - 返回 `200`
  - `Content-Type` 为 `text/html`
  - HTML 中包含关键元素 id（例如 `id="status"`、`/status`）
- 若引入 `/static/...`：
  - 增加一个静态资源（css 或 js）的返回测试（`200` + `Content-Type` 正确）

## Assumptions & Decisions

- **决定：** 采用“静态 HTML（无新依赖/无构建）”方案；不引入 React/Vue/Jinja2。
- **假设：** 首次配置页的动态数据全部来自 `/status`，不需要服务端模板注入；因此静态页面即可满足需求。
- **安全约束：** 页面与 `/status` 不回显 Cookie 明文；仅展示 session/status/verification_url 等引导信息。

## Verification Steps

- 运行单测：
  - `uv run python -m unittest discover -s tests -p 'test_*.py'`
- 手工验证：
  - 清空 `.env` 的 `XIANYU_COOKIE`，启动 `uv run xianyu-mcp --http`
  - 自动打开首次配置页，确认：
    - 二维码正常显示
    - `face_qr_data_url` 为空时不出现破图
    - 触发 `verification_required` 时右侧区域显示链接与二维码

