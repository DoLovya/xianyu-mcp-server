## 1. Python 纯函数实现

- [x] 1.1 实现 `generate_sign` — 用 `hashlib.md5` 替代 execjs
- [x] 1.2 实现 `generate_mid` — 用 `random` + `time` 替代 execjs
- [x] 1.3 实现 `generate_uuid` — 用 `time` 替代 execjs
- [x] 1.4 实现 `generate_device_id` — 用 `uuid.uuid4` 替代 execjs
- [x] 1.5 替换 `decrypt` — 用 `msgpack.unpackb` 替代 execjs 调用 JS
- 注：1.5 后原 execjs 条件导入块、`blackboxprotobuf` 依赖全部移除

## 2. 依赖清理

- [x] 2.1 更新 `pyproject.toml`：移除 `PyExecJS` + `blackboxprotobuf`，添加 `msgpack`

## 3. 文档同步

- [x] 3.1 更新 `README.md` 环境要求，去掉 `Node.js 18+`
- [x] 3.2 确认 `README.md` 中不再提及 Node.js 作为运行必需

## 4. 验证

- [x] 4.1 用 Python msgpack 对两条真实 WebSocket 消息解码成功，输出与 JS 版本一致
- [ ] 4.2 `uv sync` 确认依赖变更生效（需本机终端执行）
- [ ] 4.3 启动 MCP 服务，调用 `validate_login` 确认签名链路正常（需本机终端执行）
