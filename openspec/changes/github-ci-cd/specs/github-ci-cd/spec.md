## ADDED Requirements

### Requirement: CI workflow runs on PR and push
仓库 MUST 提供一个 GitHub Actions CI 工作流，在 Pull Request 与 push 到默认分支时自动运行，并将结果作为可用于分支保护的状态检查。

#### Scenario: PR triggers CI checks
- **WHEN** 新建或更新 Pull Request
- **THEN** CI 工作流自动运行并在 GitHub PR 页面展示结果（成功/失败）

#### Scenario: Push to default branch triggers CI checks
- **WHEN** 向默认分支 push 提交
- **THEN** CI 工作流自动运行并在 Actions 记录中可追溯

### Requirement: CI installs dependencies with uv and respects lockfile
CI MUST 使用 `uv` 安装与运行依赖，并优先以 `uv.lock` 作为冻结依赖来源以保证可重复构建；同时 MUST 支持通过环境变量覆盖索引源以适配网络环境。

#### Scenario: Frozen install by default
- **WHEN** CI 工作流执行依赖安装步骤
- **THEN** 依赖安装默认以 lockfile 冻结模式执行，确保同一提交在不同 runner 上得到一致依赖解析结果

#### Scenario: Index override for constrained networks
- **WHEN** 通过 workflow/env 配置 `UV_INDEX_URL`（或等价覆盖参数）
- **THEN** CI 使用配置后的索引源完成依赖安装

### Requirement: CI executes unit tests
CI MUST 执行仓库单元测试（当前基于 `unittest`），并在失败时使工作流失败。

#### Scenario: Test suite passes
- **WHEN** CI 执行测试命令（例如 `python -m unittest`）
- **THEN** 所有测试通过且 job 返回成功

#### Scenario: Test suite fails
- **WHEN** CI 执行测试命令且存在失败用例
- **THEN** job 返回失败并在 Actions/PR 检查中显示失败原因

### Requirement: CI performs build verification and uploads artifacts
CI MUST 进行 Python 包构建校验（wheel 与 sdist），并将 `dist/` 产物作为 workflow artifact 上传以便审计与复用。

#### Scenario: Build artifacts are produced
- **WHEN** CI 执行构建步骤
- **THEN** 生成 wheel 与 sdist 产物并写入 `dist/`

#### Scenario: Build artifacts are uploaded
- **WHEN** 构建产物生成完成
- **THEN** CI 上传 `dist/` 为 Actions artifact，供后续下载与排查

### Requirement: Release workflow produces and publishes release artifacts
仓库 MUST 提供一个 Release 工作流，在符合版本规范的 tag/release 触发时构建发布产物，并将构建产物上传为 GitHub Release 附件；仓库 SHOULD 支持发布到 PyPI（优先 Trusted Publishing，其次 API Token）。

#### Scenario: Tag triggers release build and GitHub release assets
- **WHEN** 推送一个符合规范的版本 tag（例如 `vX.Y.Z`）
- **THEN** Release 工作流构建产物并将 `dist/*` 上传为 GitHub Release 附件

#### Scenario: Optional publish to PyPI
- **WHEN** 仓库配置了 PyPI 发布所需的 Trusted Publishing 或 `PYPI_API_TOKEN`
- **THEN** Release 工作流将构建产物发布到 PyPI（或等价制品仓库）

### Requirement: Repository provides CI/CD operations documentation
仓库 MUST 提供 CI/CD 运维文档，覆盖工作流触发方式、所需 Secrets、发布与回滚流程、分支保护推荐配置与常见故障排查。

#### Scenario: Maintainer can follow documented release steps
- **WHEN** 维护者按照文档执行发布流程（tag/release）
- **THEN** 可在不阅读工作流源码的情况下完成一次可重复的发布

### Requirement: Optional security and dependency automation
仓库 SHOULD 提供基础安全与依赖自动化（如 Dependabot、CodeQL），并能以最小成本启用/禁用。

#### Scenario: Dependabot opens dependency update PRs
- **WHEN** 启用 Dependabot 配置
- **THEN** GitHub 自动创建依赖升级 Pull Request 并触发 CI 校验

#### Scenario: CodeQL runs on schedule
- **WHEN** 启用 CodeQL 工作流并到达计划时间
- **THEN** 自动执行扫描并在 Security 页面生成报告
