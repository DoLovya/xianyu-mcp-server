## Context

现状问题由两部分组成：

- **状态推进不稳定**：`QRLoginManager.generate()` 在内部通过 `asyncio.create_task(self._monitor_qr_status(...))` 启动后台轮询，但在 first_run_setup 场景中，`generate()` 是通过 `asyncio.run()` 执行的；`asyncio.run()` 结束会关闭事件循环，导致后台 task 被取消，从而会话状态长期停留在 `waiting`，最终被动 `expired`。
- **m_h5_tk 预热告警频繁**：`_get_mh5tk()` 依赖首次请求返回的 cookie；在网络/风控/服务端行为变化时可能拿不到 token，于是打印 warning 并降级继续，影响排障信噪比。

约束：

- 不改变既有 MCP 工具函数签名（兼容已接入客户端）
- 不输出/记录 Cookie 明文（仅记录长度、是否包含关键字段）

## Goals / Non-Goals

**Goals:**

- 在所有调用场景下确保二维码登录会话能稳定推进（尤其是 first_run_setup 内部调用）
- 确保进入 `verification_required`、`scanned`、`success` 等关键状态时可观测
- 将 m_h5_tk 预热从“单次失败就 warning”改为“有限重试 + 失败降级但尽量不告警”

**Non-Goals:**

- 不保证绕过所有风控/人脸验证（只保证流程与可观测性稳定）
- 不引入额外第三方依赖

## Decisions

1) **用后台线程承载二维码会话轮询（推荐且最小侵入）**

- 在 `generate()` 完成二维码生成后，启动一个守护线程，线程内独立运行一个事件循环并执行 `_monitor_qr_status(session_id)`，从而不依赖调用方事件循环是否常驻。
- 这样 first_run_setup（`asyncio.run()`）与 MCP 工具调用（常驻事件循环）两种模式都稳定。

备选：

- “get_status 触发轮询推进”方案无需线程，但依赖调用频率且会把网络 IO 挂到同步 `get_status()` 上，调用方与性能语义更复杂。

2) **避免 monitor 内部 create_task + return 的“半途退出”**

- 当前 `_monitor_qr_status()` 在确认登录后会 `create_task(_monitor_mtop_bootstrap)` 并 return；在“线程内事件循环”模型下，这会导致循环结束并取消后续任务。
- 调整为：在 `_monitor_qr_status()` / `run_face_verification()` 内直接 `await _monitor_mtop_bootstrap()`（或在必要时 `await` 人脸验证流程），确保最终状态可达（`success/verification_required/expired/error`）。

3) **m_h5_tk 预热增强：有限重试 + 更稳健 cookie 捕获**

- 在 `_get_mh5tk()` 内增加 2~3 次重试（短延迟退避）
- cookie 捕获改为优先从 `client.cookies` 同步回 `session.cookies`（而不只依赖 `resp.cookies`），并兼容 POST 响应返回的更新 cookie
- 失败继续降级，但默认仅在 DEBUG 输出原因；INFO/WARN 仅保留一次汇总

## Risks / Trade-offs

- **[线程资源]** 每个会话一个守护线程 → 通过会话过期（300s）与单进程并发量（通常很低）控制风险；必要时可加并发上限或复用线程池
- **[风控不可控]** m_h5_tk 与 mtop cookie 补齐存在服务端策略变动 → 通过重试、可观测性增强来降低不确定性影响

