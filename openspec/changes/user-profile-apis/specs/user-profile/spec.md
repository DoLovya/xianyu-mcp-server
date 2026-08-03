## Spec: User Profile (My)

### MCP Tool

- Name: `get_my_profile`
- Args: none
- Read/Write: read

### Behavior

- 调用闲鱼 PC Web 的 MTop 接口 `mtop.idle.web.user.page.nav` 获取当前登录用户的个人页数据。
- 必须通过 `RequestGuardrails.run_read` 执行。
- 返回值必须包含：
  - `success`: `bool`
  - `profile`: `object`（尽力提取的结构化字段；缺失字段允许为 `null` 或不出现）
  - `raw`: `object`（接口原始响应，完整透传）

### Recommended `profile` Fields (Best-effort)

- `user_id`
- `nick`
- `avatar_url`
- `location`
- `seller_level`
- `seller_score`

### Error Handling

- 若接口返回非 SUCCESS 或请求失败：按现有 `pyxianyu` 方式抛错并由 MCP 返回错误信息。
- 不得在日志或返回中输出完整 Cookie / Token（允许输出脱敏预览）。
