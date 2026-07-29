## 1. 策略与配置

- [x] 1.1 盘点现有 MCP 工具并划分 READ/WRITE 分类（按 `request-guardrails` 规范落表）
- [x] 1.2 设计并确定环境变量列表与默认值（READ/WRITE 间隔、抖动、退避上限、冷却时长）

## 2. 护栏核心实现

- [x] 2.1 新增进程内护栏模块（限速 + 抖动 + WRITE 串行）
- [x] 2.2 实现指数退避（可疑失败计数、退避时间窗、抖动）
- [x] 2.3 实现熔断与冷却（识别 `FAIL_SYS_USER_VALIDATE` 并阻止后续 WRITE）
- [x] 2.4 统一错误返回形式：被护栏阻止时不向闲鱼发起请求，并返回清晰错误信息（不包含敏感信息）

## 3. 工具接入

- [x] 3.1 在 `XianYuApiTools` 中为所有工具接入统一护栏入口（调用前限速/抖动，失败后更新退避/熔断状态）
- [x] 3.2 为 `edit_item/downshelf_item/reshelf_item/publish_physical_item/send_*` 等 WRITE 工具确保串行与冷却期拦截
- [x] 3.3 为 `validate_login/refresh_login/list_* /get_*` 等 READ 工具接入 READ 策略

## 4. 测试与验证

- [x] 4.1 添加单元测试覆盖：READ/WRITE 最小间隔、抖动范围、指数退避增长、熔断冷却拦截（使用标准库测试框架）
- [ ] 4.2 本地手工回归：连续调用 `edit_item → downshelf_item → reshelf_item`，确认请求被拉开且出现风控信号时进入冷却
