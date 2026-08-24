# CI/CD（GitHub Actions）

本仓库使用 GitHub Actions 实现 CI（PR 质量门禁）与 Release（发版产物发布）。工作流文件位于 `.github/workflows/`。

## 1. CI：`.github/workflows/ci.yml`

### 1.1 触发条件

- `pull_request`：PR 新建/更新
- `push`：push 到 `main` / `master`

### 1.2 做了什么

- 使用 `uv` 安装依赖：`uv sync --frozen`
- 执行单元测试：`uv run python -m unittest discover -s tests -p 'test_*.py'`
- 构建校验（wheel + sdist）：`python -m build`
- 上传构建产物：`dist/` 作为 Actions artifact

### 1.3 可配置项（Repository Variables）

用于网络环境不稳定或需要自定义 PyPI 镜像时：

- `UV_INDEX_URL`：主索引源（可选）
- `UV_EXTRA_INDEX_URL`：额外索引源（可选）

## 2. Release：`.github/workflows/release.yml`

### 2.1 触发条件

- `push` tag：匹配 `v*`（建议使用语义化版本：`vX.Y.Z`）
- `workflow_dispatch`：手动触发（可选指定 `tag`）

### 2.2 发布前校验

release workflow 会做两件事：

- 校验 tag 格式为 `vX.Y.Z`
- 校验 `pyproject.toml` 的 `[project].version` 与 tag 一致

不满足时会直接失败，避免“版本号不一致导致的不可追溯发布”。

### 2.3 GitHub Release 产物

workflow 会构建并把 `dist/*` 作为 GitHub Release 附件上传。

### 2.4 PyPI 发布

本仓库使用与 `third_party/pyxianyu` 对齐的 **Trusted Publishing** 路径。

- 依赖 OIDC，无需长期保存 PyPI Token
- 需要在 PyPI 项目配置中允许该 GitHub 仓库发布（PyPI 侧配置一次即可）
- 发布 workflow 使用标准 Python 打包链路（`python -m build` / `twine check` / `python -m venv`），不依赖 `uv sync --frozen`

默认行为：

- 推送符合规范的 `v*` tag 时，workflow 会自动尝试通过 Trusted Publishing 发布到 PyPI
- `workflow_dispatch` 保留为补发 / 重试入口；手动触发时填写已有 tag 即可

说明：

- 主路径是 `push v* tag` 自动发布，策略与 `third_party/pyxianyu` 对齐
- 手动触发 `workflow_dispatch` 时，页面里选择的 branch 仅用于加载 workflow 文件；真正发布的目标版本以 `tag` 输入为准，workflow 会显式切换到该 tag 再执行构建与发布
- 当前发布流程已移除 `PYPI_API_TOKEN` 兜底分支，避免额外的条件分支和配置漂移

### 2.5 回滚 / 撤回发布（建议流程）

- GitHub Release：在 Releases 页面将对应 Release 标记为 Draft 或删除（不会删除 git tag）
- Git tag：
  - 如需撤回 tag，可删除远端 tag 并同步删除本地 tag
  - 已被下游依赖引用的 tag 不建议删除，优先发一个新的修复版本（例如 `vX.Y.(Z+1)`）
- PyPI：
  - 依 PyPI 政策，已发布版本通常不允许覆盖上传
  - 如发布错误，推荐发一个新的修复版本；必要时使用 yanked（撤回但保留可追溯）策略

## 3. 安全与依赖治理（可选）

### 3.1 Dependabot

配置文件：`.github/dependabot.yml`

建议流程：

- Dependabot 提 PR → CI 自动跑 → 合并后本地执行 `uv lock` 更新 `uv.lock`（如需锁文件变更）

### 3.2 CodeQL

配置文件：`.github/workflows/codeql.yml`

说明：

- CodeQL 需要 GitHub 仓库启用 Code Scanning（Security 页面可查看结果）
- 如不需要，可直接删除/禁用该 workflow

## 4. 分支保护（推荐配置）

在 GitHub 仓库 Settings → Branches → Branch protection rules：

- Require a pull request before merging
- Require status checks to pass before merging
  - 勾选 CI 相关检查（例如 `Test (Python 3.11)`、`Build (Python 3.11)`）
- Require linear history（可选）
- Restrict who can push to matching branches（按团队需要）

## 5. 常见问题

### 5.1 CI 安装依赖失败

- 优先检查网络与索引源
- 必要时设置 `UV_INDEX_URL` / `UV_EXTRA_INDEX_URL` 以切换镜像

### 5.2 Release 失败：tag 与版本不一致

- 确保先更新 `pyproject.toml` 的版本号，再打 tag
- 推荐流程：
  - 修改版本号 → 合并到 main → 打 tag `vX.Y.Z` 推送
