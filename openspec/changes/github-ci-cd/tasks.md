## 1. CI（PR / Push 质量门禁）

- [x] 1.1 新增 `.github/workflows/ci.yml`：配置触发器（pull_request、push 到默认分支）
- [x] 1.2 在 `ci.yml` 中配置 Python 版本矩阵（>=3.11）并安装 `uv`
- [x] 1.3 在 `ci.yml` 中执行 `uv sync --frozen`（并支持 `UV_INDEX_URL` 覆盖）完成依赖安装
- [x] 1.4 在 `ci.yml` 中执行单元测试（`uv run python -m unittest`）
- [x] 1.5 在 `ci.yml` 中执行构建校验（构建 wheel + sdist）
- [x] 1.6 在 `ci.yml` 中上传 `dist/` 作为 workflow artifact
- [x] 1.7（可选）为 CI 添加并行/缓存优化（例如 uv cache、pip cache），并固化 Action 版本

## 2. CD（Release / Tag 发版）

- [x] 2.1 新增 `.github/workflows/release.yml`：配置触发器（`push` tag `v*` 或 `workflow_dispatch`）
- [x] 2.2 在 `release.yml` 中复用构建步骤生成 `dist/` 并上传到 GitHub Release（作为附件）
- [x] 2.3 配置 PyPI 发布路径（两选一）：
  - [x] 2.3.1 优先：PyPI Trusted Publishing（OIDC）所需的 GitHub/PyPI 配置与文档
  - [x] 2.3.2 备选：使用 `PYPI_API_TOKEN` Secret 的发布步骤与文档
  - [x] 2.3.3 对齐 `third_party/pyxianyu` 的发版策略：移除 `PUBLISH_PYPI_ON_TAG` 条件开关，使 `push v* tag` 默认自动发布到 PyPI
- [x] 2.4 增加“发布前校验”步骤（版本号规范、tag 规范、构建产物存在性校验）
- [x] 2.5 增加“回滚/撤回发布”建议流程（文档化）

## 3. 安全与依赖治理（可选但推荐）

- [x] 3.1 新增 `.github/dependabot.yml`：配置 Python 依赖升级 PR（频率、分组策略）
- [x] 3.2 新增 `.github/workflows/codeql.yml`：配置 CodeQL 扫描（按需开启与运行频率）
- [x] 3.3 在文档中说明安全工作流的启用/禁用方式与维护责任边界

## 4. 文档与仓库策略

- [x] 4.1 新增 `docs/ci-cd.md`：写清楚 CI/CD 的触发器、运行内容、所需 Secrets、发布/回滚、故障排查
- [x] 4.2 更新 README：增加 CI 状态徽章（badge）与最短发布步骤指引（链接到 `docs/ci-cd.md`）
- [x] 4.3 输出 Branch Protection 推荐配置清单（需要勾选哪些 Required checks、是否允许管理员绕过等）

## 5. 验证与交付

- [ ] 5.1 在一个测试分支触发 CI（PR）并确认所有 job 通过且产物可下载
- [ ] 5.2 使用测试 tag 或 `workflow_dispatch` 验证 release 流水线，确认 GitHub Release 附件与 PyPI 自动发布路径都成功
- [x] 5.3 汇总交付物清单（新增文件列表、Secrets 列表、触发器列表）并在 PR 描述中对齐
