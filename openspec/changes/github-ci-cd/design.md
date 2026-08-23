## Context

- 项目：`xianyu-mcp`（Python ≥ 3.11），基于 `pyproject.toml` + `hatchling` 构建，运行/依赖管理使用 `uv`（仓库存在 `uv.lock`）。
- 当前状态：仓库缺少 `.github/workflows/`，PR 合并与发版无自动化保障。
- 约束：
  - 测试框架当前为 `unittest`（`tests/` 下已有测试），CI 需要以最小依赖可运行作为第一目标
  - 需兼顾国内/国际网络环境差异（`uv.lock` 可能包含镜像源信息），工作流需要可配置索引源

## Goals / Non-Goals

**Goals:**

- 引入可落地的 GitHub Actions CI：在 PR / push 上自动执行可重复的校验（依赖安装、单测、基础构建）
- 引入可落地的 GitHub Actions CD：在 tag/release 上自动构建并发布产物（至少 GitHub Release 附件；可选 PyPI 发布）
- 提供完整文档：覆盖工作流触发方式、Secrets、发布/回滚流程、分支保护建议与故障排查

**Non-Goals:**

- 不在本变更中实现“部署到服务器/云运行环境”的自动化（如自建服务、K8s、云函数等）
- 不强制引入新的代码质量工具链（ruff/mypy 等），但会在方案中预留可插拔扩展点

## Decisions

1. **工作流拆分**
   - `ci.yml`：PR / push 触发的质量门禁（单测 + 构建校验）
   - `release.yml`：tag/release 触发的发版流水线（构建 + 发布/上传）
   - `security.yml`（可选）：CodeQL 扫描（按需开启）
   - `dependabot.yml`（可选）：依赖自动升级 PR（按需开启）

2. **Python & 依赖安装策略**
   - 采用 GitHub 官方 `actions/setup-python` 提供 Python 运行时
   - 采用 `uv` 作为依赖安装与运行入口（与本仓库当前使用方式一致）
   - CI 默认使用 `uv sync --frozen`（锁定依赖、可重复）；同时允许通过 `UV_INDEX_URL`/`UV_EXTRA_INDEX_URL` 覆盖索引源，以适配不同网络环境

3. **测试与构建命令（最小可行）**
   - 测试：`uv run python -m unittest`（与现有 `tests/` 兼容）
   - 构建：使用 PEP 517 标准构建（`python -m build`），并将 `dist/` 作为 workflow artifact 上传，便于排查与供 release 复用

4. **发布策略（CD）**
   - GitHub Release：在 `v*` tag 时将 `dist/*` 上传为 Release 附件
   - PyPI 发布：主仓库发布策略与 `third_party/pyxianyu` 对齐。对于合法的 `v*` tag，release workflow 默认直接执行 PyPI 发布，不再依赖 `PUBLISH_PYPI_ON_TAG` 这类额外仓库变量开关
   - 手动触发：保留 `workflow_dispatch`，但用途收敛为补发、重试或故障恢复，而不是日常正式发布入口
   - 发布认证：优先使用 PyPI Trusted Publishing（OIDC，无需长期 token）；若无法启用，则退化为 `PYPI_API_TOKEN` Secret

5. **为什么不保留额外开关**
   - 当前主仓库多了一层 `vars.PUBLISH_PYPI_ON_TAG == '1'` 条件，带来的主要问题不是安全性，而是可观察性差：维护者看到 tag、GitHub Release 和 CI 都成功后，仍可能误以为 PyPI 已发布
   - `pyxianyu` 的策略更单义：tag push 就是正式发布，失败就明确失败，没有“部分成功”的灰色状态
   - 因此主仓库应采用同样的策略，把“是否发布 PyPI”这个决策前移到“是否推送正式 tag”，而不是放在 workflow 内部再加一层开关判断

6. **分支保护建议**
   - 建议开启 Branch Protection：要求 `ci.yml` 的关键 job 全部通过才能合并到默认分支
   - 建议开启“Require linear history / Require PR reviews”等（最终以团队协作模式为准）

## Risks / Trade-offs

- [uv.lock 索引源不可达] → 通过 `UV_INDEX_URL` 可配置，并在文档中提供推荐配置；必要时允许 CI 使用 `uv sync` 非 frozen 模式作为应急开关
- [外部 Action 供应链风险] → 尽量 pin 到明确版本（tag 或 commit SHA），并在安全章节说明维护策略
- [发版误触发] → release workflow 仅允许 `v*` tag 或手动触发；并在文档中明确 tag 规范与回滚手段。自动发布到 PyPI 的前提是“推送 tag 即视为正式发版”
- [Secrets 泄漏风险] → 最小权限原则；尽量使用 OIDC；严格禁止在日志打印敏感信息
- [旧变量残留造成误导] → 从文档、workflow 条件和发布手册中同时移除 `PUBLISH_PYPI_ON_TAG`，避免维护者以为仍需额外配置

## Migration Plan

1. 调整主仓库 `release.yml`，删除 `push tag` 场景下对 `PUBLISH_PYPI_ON_TAG` 的条件判断
2. 保留 `workflow_dispatch`，仅作为补发/重试路径
3. 更新 `docs/ci-cd.md` 与发布文档，明确“正式 tag = 自动发布 PyPI”
4. 使用测试 tag 或 `workflow_dispatch` 验证 PyPI 发布路径是否与 `pyxianyu` 一致

## Open Questions

- 无。当前方向明确：主仓库发布策略直接对齐 `pyxianyu`
