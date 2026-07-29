## Summary

使用 OpenSpec CLI 的 `openspec archive` 命令，将当前仓库 `openspec/changes/` 下**已完成（tasks 全部勾选）**的 change 归档到 `openspec/changes/archive/`。

本次按你的选择，仅归档：
- `edit-item-tool`
- `remove-nodejs-dependency`

保留未完成的 change（不归档）：
- `anti-bot-rate-limit`（缺 4.2 手工回归）
- `publish-physical-item`（缺 Task 6 实际发布）

## Current State Analysis

仓库路径：`/Users/huan.zhang/Code/xianyu-mcp-server/openspec`

### Change 完成度（基于 tasks.md）
- `edit-item-tool`：Task 1~3 均为 `[x]`（已完成）
- `remove-nodejs-dependency`：1.1~4.3 均为 `[x]`（已完成）
- `anti-bot-rate-limit`：4.2 为 `[ ]`（未完成）
- `publish-physical-item`：Task 6 为 `[ ]`（未完成）

### Spec Sync 评估
当前仓库不存在 `openspec/specs/<capability>/spec.md` 的“主规格目录”，各 change 的规格文件均位于对应 change 目录下（例如 `openspec/changes/edit-item-tool/specs/item-edit/spec.md`）。

因此本次归档不涉及 `openspec sync`（没有可同步的“主规格”目标）。

## Proposed Changes

### 1) 归档前检查（只读）

分别检查 change 状态与任务是否全完成：

```bash
openspec status --change "edit-item-tool" --json
openspec status --change "remove-nodejs-dependency" --json
```

并确认对应 `tasks.md` 中不存在任何 `- [ ]` 未完成项：

- `openspec/changes/edit-item-tool/tasks.md`
- `openspec/changes/remove-nodejs-dependency/tasks.md`

### 2) 执行归档（写操作：移动目录）

依次归档两个已完成 change：

```bash
openspec archive "edit-item-tool"
openspec archive "remove-nodejs-dependency"
```

预期结果：
- `openspec/changes/archive/YYYY-MM-DD-edit-item-tool/` 出现
- `openspec/changes/archive/YYYY-MM-DD-remove-nodejs-dependency/` 出现
- 原 `openspec/changes/edit-item-tool/` 与 `openspec/changes/remove-nodejs-dependency/` 目录不再存在（已移动）

### 3) 归档后验证（只读）

```bash
openspec list
```

预期结果：
- 列表中不再出现 `edit-item-tool`、`remove-nodejs-dependency`
- 仍保留 `anti-bot-rate-limit`、`publish-physical-item`

## Assumptions & Decisions

- 仅归档 tasks 全部完成的 change（按你选择的“仅归档已完成”）
- 不对 `anti-bot-rate-limit` / `publish-physical-item` 做“强行归档”
- 不做 spec sync：当前仓库未建立 `openspec/specs/` 主规格目录

## Verification Steps

- `openspec list` 确认 active changes 只剩未完成的两个
- 检查 `openspec/changes/archive/` 下归档目录存在且包含原 change 文件（proposal/design/specs/tasks/.openspec.yaml）
