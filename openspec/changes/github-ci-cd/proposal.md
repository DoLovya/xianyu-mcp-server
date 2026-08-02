## Why

当前仓库缺少 GitHub 原生 CI/CD，导致以下问题：

- PR 质量不可控：缺少自动化测试/基础校验，回归风险高
- 发版不可重复：手工打包/发布容易漏步骤、难追溯
- 缺少安全与依赖治理：无法自动检查高危依赖、无法统一升级策略

## What Changes

- 新增 GitHub Actions 工作流（`.github/workflows/*.yml`）：
  - CI：在 PR / push 时自动执行安装、单元测试、基础构建校验，并产出构建产物供排查
  - CD（Release）：在 tag/release 触发时自动构建并发布 Python 包（可选发布到 PyPI），并生成 GitHub Release 附件
  - 安全与依赖治理：CodeQL（可选）、Dependabot（可选）等基础安全/依赖自动化
- 增加 CI/CD 文档与运维手册：
  - 工作流说明、触发条件、所需 Secrets、发布流程、回滚策略、常见故障排查
  - 推荐的分支保护（Branch Protection）与必需检查项配置
-（可选）补齐工程化工具链以便 CI 稳定运行：
  - 明确测试入口（`python -m unittest`）与最小可行质量门槛
  - 如需要 lint/format/typecheck，再引入对应工具与配置（例如 ruff/mypy），并纳入 CI

## Capabilities

### New Capabilities

- `github-ci-cd`: 为本仓库提供可复用、可验证的 GitHub Actions CI/CD 能力（CI、Release、依赖/安全治理与文档化运维）

### Modified Capabilities

- （无）

## Impact

- 新增目录：`.github/workflows/`（CI/CD 工作流定义）
- 可能新增/调整文档：README 或新增 `docs/ci-cd.md`（最终以 design/tasks 为准）
- 可能新增仓库配置约定：
  - GitHub Secrets（如 `PYPI_API_TOKEN` 等）
  - 分支保护规则（要求 CI 通过才能合并）
  - Release/tag 规范（语义化版本、tag 命名等）
