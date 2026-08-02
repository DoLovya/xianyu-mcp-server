## Summary

盘点当前仓库 `openspec/changes/` 下未归档（active）的 OpenSpec 变更，并标出每个变更在 `tasks.md` 中仍未完成的任务条目（`- [ ]`）。

## Current State Analysis

当前 `openspec/changes/` 下存在 4 个 active 变更：

- `anti-bot-rate-limit`
- `github-ci-cd`
- `publish-physical-item`
- `trae-config-text-input`

其中 `archive/` 目录下的变更均为已归档历史记录，不在本次“未完成”范围。

## Pending Changes (Not Archived)

### 1) github-ci-cd

**未完成任务（2 项）**

- 5.1 在一个测试分支触发 CI（PR）并确认所有 job 通过且产物可下载
- 5.2 使用 `workflow_dispatch` 或测试 tag 验证 release 流水线（至少 GitHub Release 附件成功）

**备注**

- 这两项属于“需要 GitHub Actions 真实跑一次才能确认”的验证任务，本地无法替代完成。

### 2) anti-bot-rate-limit

**未完成任务（1 项）**

- 4.2 本地手工回归：连续调用 `edit_item → downshelf_item → reshelf_item`，确认请求被拉开且出现风控信号时进入冷却

**备注**

- 该项需要具备可用 Cookie 的运行环境与可重复的写操作测试路径（注意写操作必须串行执行）。

### 3) trae-config-text-input

**未完成任务（3 项）**

- 1.1 更新 `.trae/mcp.json`：为 `xianyu-mcp-server` 增加 `env.XIANYU_COOKIE` 与 `env.XIANYU_COOKIE_FILE` 占位（如受限制请手工补齐）
- 1.2 校验 Trae UI 可在 MCP Server 配置界面展示对应输入框，并能随 env 启动服务端
- 3.2 手工冒烟：清空 `.env`，在 Trae UI 输入 `XIANYU_COOKIE` 后调用 `validate_login` 成功

**备注**

- 1.2 / 3.2 强依赖 Trae 客户端侧 UI 与启动行为，属于“集成验证”类任务。

### 4) publish-physical-item

**未完成任务（0 项）**

- `tasks.md` 中没有 `- [ ]` 未勾选条目（仅表示 tasks 已完成；仍处于 active 说明尚未执行归档流程）

## Proposed Next Actions

1. 完成并勾选 `github-ci-cd` 的 5.1 / 5.2（GitHub Actions 实跑确认）
2. 完成并勾选 `anti-bot-rate-limit` 的 4.2（本地串行写操作回归）
3. 完成并勾选 `trae-config-text-input` 的 1.1 / 1.2 / 3.2（Trae UI 集成验证）
4. 对 `publish-physical-item` 执行归档（无未完成 tasks）
5. 以上变更 tasks 全部完成后，统一执行 OpenSpec 归档（archive）

## Verification Steps

- 对每个 active change：
  - 检查 `openspec/changes/<change>/tasks.md` 中 `- [ ]` 数量为 0
- 对需要线上验证的变更：
  - `github-ci-cd`：确认 Actions 页面 CI / Release 都成功，artifact 与 Release 附件可下载
  - `trae-config-text-input`：确认 Trae UI 输入后，服务端读取到 env 并 `validate_login` 成功
- 最终将已完成的 change 移入 `openspec/changes/archive/YYYY-MM-DD-<name>/`
