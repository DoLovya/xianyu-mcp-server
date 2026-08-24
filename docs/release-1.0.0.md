# xianyu-mcp-server 1.0.0 发布文档

本文档用于指导 `xianyu-mcp-server` 首个正式版本 `1.0.0` 的发布，覆盖发布前检查、GitHub 配置、PyPI 配置、正式发布流程与回滚策略。

## 1. 发布目标

`1.0.0` 是本项目首个正式对外版本，发布目标如下：

- PyPI 包名固定为 `xianyu-mcp-server`
- CLI 入口命令固定为 `xianyu-mcp-server`
- `xianyu_mcp.__version__` 能正确读取 `1.0.0`
- GitHub Release 附带 wheel / sdist 构建产物
- PyPI 发布后可通过最终用户方式安装并启动

## 2. 发布前置条件

发布前需要确认以下条件全部满足。

### 2.1 代码与版本

- 仓库根目录 `pyproject.toml` 中 `[project].version` 为 `1.0.0`
- `third_party/pyxianyu/pyproject.toml` 中 `[project].version` 为 `1.0.0`
- `pyproject.toml` 中 `[project.scripts]` 仅保留 `xianyu-mcp-server`
- `README.md` 中的安装命令已使用：

```bash
uvx --from xianyu-mcp-server xianyu-mcp-server
```

### 2.2 PyPI Trusted Publishing

推荐使用 PyPI Trusted Publishing，不依赖长期保存的 API Token。

需要在 PyPI 项目中预先完成可信发布者配置，绑定当前 GitHub 仓库：

- GitHub Repository Owner: `DoLovya`
- GitHub Repository Name: `xianyu-mcp-server`
- Workflow 文件：`.github/workflows/release.yml`

如果 PyPI 端未完成 Trusted Publisher 配置，即使 GitHub Actions 运行到发布步骤，也会在 PyPI 发布阶段失败。

## 3. 发布前自检

发布前必须先运行：

```bash
python scripts/release_checklist.py
```

该脚本会执行以下检查：

- `pyproject.toml` 元数据一致性检查
- `src/` 与 `third_party/pyxianyu/src/` 的语法检查
- `xianyu-mcp-server` 单元测试
- `pyxianyu` 单元测试
- wheel 构建
- 干净虚拟环境安装态冒烟验证

全部通过后，才允许继续打 tag。

## 4. 正式发布流程

### 4.1 本地执行自检

```bash
python scripts/release_checklist.py
```

### 4.2 创建 release tag

推荐使用带注释 tag：

```bash
git tag -a v1.0.0 -m "Release xianyu-mcp-server 1.0.0"
git push origin v1.0.0
```

如本机已配置 GPG，也可使用签名 tag：

```bash
git tag -s v1.0.0 -m "Release xianyu-mcp-server 1.0.0"
git push origin v1.0.0
```

### 4.3 GitHub Actions 自动执行内容

推送 `v1.0.0` 后，`.github/workflows/release.yml` 会自动执行：

1. checkout 指定 tag
2. `uv sync --frozen`
3. 校验 tag 格式为 `vX.Y.Z`
4. 校验 tag 与 `pyproject.toml` 版本一致
5. 构建 wheel 与 sdist
6. 在干净环境安装 wheel 并执行冒烟测试
7. 创建 GitHub Release 并上传 `dist/*`
8. 自动尝试发布到 PyPI

## 5. PyPI 发布触发规则

当前 workflow 支持两种方式发布到 PyPI。

### 5.1 方式 A：tag 自动发布

满足以下条件时，push tag 会自动发布：

- 推送的是 `v*` tag，例如 `v1.0.0`
- 仓库已配置 PyPI Trusted Publishing

### 5.2 方式 B：手动触发 workflow

在 GitHub Actions 页面手动运行 Release workflow，并设置：

- `tag = v1.0.0`
- `publish_pypi = true`
- `pypi_via_token = false`

此模式仍然依赖 PyPI Trusted Publishing。
页面里选择的 branch 仅用于加载 workflow 文件，真正发布的目标版本以 `tag` 输入为准。

### 5.3 方式 C：手动触发 + API Token

仅在 Trusted Publishing 暂不可用时作为备选方案：

- GitHub Secret：`PYPI_API_TOKEN`
- 手动运行 Release workflow
- 设置 `publish_pypi = true`
- 设置 `pypi_via_token = true`

## 6. 发布结果验证

发布完成后，至少验证以下三项。

### 6.1 GitHub Release

在仓库 Releases 页面确认：

- 出现 `v1.0.0`
- 附件中包含 `.whl` 与 `.tar.gz`

### 6.2 PyPI 页面

确认 `xianyu-mcp-server` 项目中已出现 `1.0.0` 版本。

### 6.3 最终用户安装验证

推荐执行以下命令验证真实安装链路：

```bash
uvx --from xianyu-mcp-server xianyu-mcp-server --help
```

或：

```bash
python -m pip install xianyu-mcp-server==1.0.0
xianyu-mcp-server --help
```

注意：GitHub 仓库页面右侧的 `Packages` 区域是 GitHub Packages，不代表 PyPI 发布状态，不能用它判断 PyPI 是否发布成功。

## 7. 常见问题

### 7.1 打了 tag，但没有发布到 PyPI

优先检查以下两项：

1. Release workflow 是否真的被 `push tag` 触发
2. `Publish to PyPI` 步骤是 `skipped` 还是 `failed`

判断方式：

- `skipped`：通常是你看的不是 `Release` workflow，或者只是重新创建了 GitHub Release 页面，并没有重新触发 tag push
- `failed`：通常是 PyPI Trusted Publisher 未配置好，或 PyPI 拒绝本次发布

### 7.2 GitHub Release 成功，但 PyPI 仍然没有版本

这通常说明：

- 构建和 GitHub Release 没问题
- 但 PyPI 发布步骤被跳过，或在发布阶段失败

不能因为 GitHub Release 成功，就认为 PyPI 一定发布成功。

### 7.3 tag 打错了怎么办

如果 tag 尚未被外部广泛引用，可删除后重打：

```bash
git tag -d v1.0.0
git push --delete origin v1.0.0
```

修正版本或提交后，重新创建正确 tag。

### 7.4 PyPI 上已存在错误版本怎么办

PyPI 不允许覆盖上传同版本文件。若 `1.0.0` 已错误发布，通常应：

- 保留 `1.0.0`
- 发新版本，例如 `1.0.1`

不要尝试重新上传同版本覆盖旧文件。

## 8. 回滚策略

若发布后发现严重问题，建议按影响范围处理：

1. GitHub Release 可删除或标记为草稿
2. git tag 如确有必要可删除，但已被引用时不建议这样做
3. PyPI 已发出的版本不要覆盖，优先发布修复版 `1.0.1`

## 9. 推荐操作清单

建议每次正式发布都按以下顺序执行：

1. 确认 `pyproject.toml` 版本为 `1.0.0`
2. 确认 `third_party/pyxianyu` 版本也为 `1.0.0`
3. 运行 `python scripts/release_checklist.py`
4. 确认 PyPI Trusted Publisher 已配置
5. 执行 `git tag -a v1.0.0 -m "Release xianyu-mcp-server 1.0.0"`
6. 执行 `git push origin v1.0.0`
7. 在 GitHub Actions 中确认 `Release` workflow 的 PyPI 发布步骤成功
8. 在 PyPI 页面确认 `1.0.0` 可见
9. 执行一次最终用户安装验证
