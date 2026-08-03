## Tasks

1. 证据与字段基线
   - 从 `DoLovya/XianYuClient` 抽取 `mtop.idle.web.user.page.nav` 的 URL / 参数 / data 结构，作为实现基线。

2. third_party/pyxianyu：新增 UserApi
   - 新增 `third_party/pyxianyu/apis/user_api.py`
   - 实现 `get_user_page_nav()`（无参数，data 为 `{}`）
   - 在 `third_party/pyxianyu/apis/__init__.py` 导出 `UserApi`

3. MCP：新增 get_my_profile 工具
   - 在 `src/xianyu_mcp/tools/xianyu_api_tools.py`：
     - 加载 `UserApi`
     - 增加 `get_my_profile()` 方法，走 `run_read`
     - 输出 `{ success, profile, raw }`
   - 在 `src/xianyu_mcp/tools/__init__.py` / server 注册处暴露新工具（按现有模式）

4. 测试
   - 新增单测覆盖：
     - 工具方法存在且可调用（不依赖真实网络时可用 monkeypatch）
     - 输出格式字段固定（success/profile/raw）

5. 手工验收
   - 使用真实 Cookie 调用 `get_my_profile`，确认返回包含 raw，且 profile 至少能给出 user_id（其余字段尽力提取）。
