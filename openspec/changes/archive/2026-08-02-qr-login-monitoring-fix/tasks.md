## 1. 会话监控生命周期修复

- [x] 1.1 在 QRLoginManager.generate() 中启动“守护线程 + 独立事件循环”执行 \_monitor\_qr\_status(session\_id)，避免依赖调用方事件循环存活
- [x] 1.2 重构 \_monitor\_qr\_status：确认登录后不再 create\_task 后直接 return，而是 await 后续 mtop cookie 补齐流程直到终态（success/verification\_required/expired/error）
- [x] 1.3 重构 run\_face\_verification：完成 unb/cookie 获取后 await mtop cookie 补齐流程，避免后台 task 因事件循环退出被取消

## 2. m\_h5\_tk 预热稳定性与告警降噪

- [x] 2.1 增强 \_get\_mh5tk：增加有限重试（2\~3 次），并从 client.cookies/响应 cookies 更稳健地同步回 session.cookies
- [x] 2.2 调整日志级别：m\_h5\_tk 预热失败默认改为 DEBUG 记录原因 + INFO 汇总一次（仍保留降级继续）

## 3. 验证与回归

- [x] 3.1 增补单测/可测桩：覆盖 first\_run\_setup 触发 asyncio.run(generate) 的场景，确保状态能从 waiting 推进（通过 mock 网络轮询返回）
- [x] 3.2 手工回归：启动 first\_run\_setup，扫码后日志应出现 scanned/verification\_required/success 的状态变化且不再静默 waiting→expired

