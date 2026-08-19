## 1. pyxianyu 核心请求层修复（5 处指纹消除）

- [x] 1.1 修改 `third_party/pyxianyu/src/pyxianyu/core/client.py`：`build_mtop_params` 中 `t` 改为毫秒级真实时间戳 `int(time.time() * 1000)`（而非 `int(time.time()) * 1000`）
- [x] 1.2 修改 `third_party/pyxianyu/src/pyxianyu/utils/xianyu_utils.py`：`generate_device_id(user_id)` 改为基于 `unb` 哈希的稳定值（md5 按 8-4-4-4-12 分段 + `"-" + unb` 后缀），替换原 `uuid.uuid4()` 方案

## 2. AuthApi.get_token 消除脚本特征（3 处）

- [x] 2.1 修改 `third_party/pyxianyu/src/pyxianyu/apis/auth_api.py`：`get_token` 的 `post_json(..., verify=False)` 改为不传 verify（等价 `True`），与 `refresh_token` 对齐
- [x] 2.2 修改 `AuthApi.get_token`：`build_json_headers(include_host=True)` 改为 `build_json_headers()`（默认 False，不手写 Host 头）
- [x] 2.3 修改 `AuthApi.get_token`：`max_attempts` 默认从 3 改为 1（或等价地移除内部 retry 循环），失败直接抛异常，交由外层 guardrails 退避

## 3. 验证与冒烟

- [x] 3.1 语法校验：`client.py`、`xianyu_utils.py`、`auth_api.py` 三处改动 AST 编译通过、模块可导入
- [x] 3.2 运行需求场景验证（纯逻辑，无需登录）：`t` 末三位非 000、device_id 稳定性、verify/Host 头策略对齐
- [x] 3.3 GetDiagnostics 确认无 lint/type 错误；如有 pytest 套件可运行（当前 `pytest` 不可行，跳过）
- [x] 3.4 重新尝试 MCP 工具 `validate_login` 与 `list_conversations(only_top=True)`，确认不再因为请求形态差异立即触发拦截（账号仍被硬风控需要浏览器端先解除）
