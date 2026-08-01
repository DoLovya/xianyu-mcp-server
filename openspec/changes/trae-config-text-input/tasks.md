## 1. Trae 配置输入框

- [ ] 1.1 更新 `.trae/mcp.json`：为 `xianyu-mcp-server` 增加 `env.XIANYU_COOKIE` 与 `env.XIANYU_COOKIE_FILE` 占位（如受限制请手工补齐）
- [ ] 1.2 校验 Trae UI 可在 MCP Server 配置界面展示对应输入框，并能随 env 启动服务端

## 2. 文档与安全提示

- [x] 2.1 更新 README：增加“Trae 配置（文本框输入 Cookie）”说明与示例
- [x] 2.2 README 增加安全提示：不要把包含 Cookie 的配置提交到仓库；推荐使用 `XIANYU_COOKIE_FILE` 指向本地 gitignore 文件

## 3. 回归验证

- [x] 3.1 增加单测：`_load_cookie_str` 对 `XIANYU_COOKIE`/`XIANYU_COOKIE_FILE` 的优先级符合 spec
- [ ] 3.2 手工冒烟：清空 `.env`，在 Trae UI 输入 `XIANYU_COOKIE` 后调用 `validate_login` 成功
