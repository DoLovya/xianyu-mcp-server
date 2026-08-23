#!/usr/bin/env python3
"""发布前自检脚本：pyproject 元数据、单元测试、wheel 安装态断言三件套。

直接在仓库根目录运行：
    python scripts/release_checklist.py
    # 或（推荐带 venv，确保依赖完整）
    .venv/bin/python scripts/release_checklist.py

零 heredoc，零多行粘贴，直接复制一条命令即可。任何检查不通过都会 sys.exit(1)。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PYXIANYU_ROOT = REPO_ROOT / "third_party" / "pyxianyu"


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    def ok(self, name: str, detail: str = "") -> None:
        msg = f"✅ [{name}] {detail}".rstrip()
        self.passed.append(msg)
        print(msg)

    def fail(self, name: str, reason: str) -> None:
        msg = f"❌ [{name}] {reason}".rstrip()
        self.failed.append((name, reason))
        print(msg, file=sys.stderr)


def run(cmd: list[str], *, cwd: Path | None = None, env_extra: dict[str, str] | None = None, capture: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(cmd, cwd=str(cwd or REPO_ROOT), env=env, capture_output=capture, text=True)


def check_pyproject(report: Report) -> None:
    import tomllib

    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        p = tomllib.load(f)["project"]
    with open(PYXIANYU_ROOT / "pyproject.toml", "rb") as f:
        px = tomllib.load(f)["project"]

    name = p.get("name")
    version = p.get("version")
    scripts = sorted((p.get("scripts") or {}).keys())
    px_version = px.get("version")

    print(f"\n===== 1. pyproject 元数据一致性 =====")
    print(f"  xianyu-mcp-server : name={name}, version={version}, scripts={scripts}")
    print(f"  pyxianyu          : version={px_version}")

    if name == "xianyu-mcp-server":
        report.ok("pyproject.name", "name = xianyu-mcp-server")
    else:
        report.fail("pyproject.name", f"必须是 xianyu-mcp-server，实际 {name!r}")

    if version == "1.0.0":
        report.ok("pyproject.version (xianyu-mcp-server)", "version = 1.0.0")
    else:
        report.fail("pyproject.version (xianyu-mcp-server)", f"必须是 1.0.0，实际 {version!r}")

    if scripts == ["xianyu-mcp-server"]:
        report.ok("pyproject.scripts", "仅注册 xianyu-mcp-server，无旧入口残留")
    else:
        report.fail("pyproject.scripts", f"期望 ['xianyu-mcp-server']，实际 {scripts!r}")

    if px_version == "1.0.0":
        report.ok("pyproject.version (pyxianyu)", "pyxianyu 1.0.0 与 xianyu-mcp-server 主版本一致")
    else:
        report.fail("pyproject.version (pyxianyu)", f"必须是 1.0.0，实际 {px_version!r}")


def check_compileall(report: Report) -> None:
    print(f"\n===== 2. compileall 语法检查 =====")
    targets = [str(REPO_ROOT / "src"), str(PYXIANYU_ROOT / "src"), str(PYXIANYU_ROOT / "scripts")]
    cp = run([sys.executable, "-m", "compileall", "-q", *targets])
    if cp.returncode == 0:
        report.ok("compileall", "src + scripts 0 errors")
    else:
        report.fail("compileall", cp.stdout + cp.stderr or f"exit={cp.returncode}")


def check_unittests(report: Report) -> None:
    base_env = {"PYTHONPATH": f"{REPO_ROOT / 'src'}{os.pathsep}{PYXIANYU_ROOT / 'src'}"}

    print(f"\n===== 3. 单元测试：xianyu-mcp-server =====")
    cp = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
             env_extra=base_env, capture=False)
    if cp.returncode == 0:
        report.ok("unittest.xianyu-mcp-server", "全量用例通过")
    else:
        report.fail("unittest.xianyu-mcp-server", f"exit={cp.returncode}")

    print(f"\n===== 4. 单元测试：pyxianyu =====")
    cp = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
             cwd=PYXIANYU_ROOT,
             env_extra={"PYTHONPATH": str(PYXIANYU_ROOT / "src")},
             capture=False)
    if cp.returncode == 0:
        report.ok("unittest.pyxianyu", "全量用例通过")
    else:
        report.fail("unittest.pyxianyu", f"exit={cp.returncode}")


def check_wheel_install(report: Report) -> None:
    print(f"\n===== 5. wheel 构建 + 干净 venv 安装态断言 =====")
    with tempfile.TemporaryDirectory(prefix="xianyu-mcp-release-check-") as td:
        td = Path(td)
        dist_dir = td / "dist"
        venv_dir = td / "venv"
        dist_dir.mkdir(parents=True)

        build_log = td / "build.log"
        with open(build_log, "w") as f:
            cp = run([sys.executable, "-m", "build", "--outdir", str(dist_dir)], capture=True)
            f.write("STDOUT:\n" + (cp.stdout or "") + "\n\nSTDERR:\n" + (cp.stderr or ""))
        if cp.returncode != 0:
            report.fail("wheel.build", f"exit={cp.returncode}，详情见 {build_log}")
            return

        wheels = sorted(dist_dir.glob("*.whl"))
        if not wheels:
            report.fail("wheel.build", f"build 成功但 dist 下无 .whl：{sorted(p.name for p in dist_dir.iterdir())}")
            return
        print(f"  构建产物：{wheels[0].name}")
        if "xianyu_mcp_server" not in wheels[0].name:
            report.fail("wheel.name", f"文件名必须带 xianyu_mcp_server，实际 {wheels[0].name!r}")
            return

        print("  创建干净 venv 安装 wheel ...")
        venv.create(str(venv_dir), with_pip=True, clear=True)
        venv_py = venv_dir / "bin" / "python"
        venv_bin = venv_dir / "bin"
        if not venv_py.exists():
            report.fail("wheel.venv", f"venv python 不存在：{venv_py}")
            return

        cp = run([str(venv_py), "-m", "pip", "install", "--quiet", str(wheels[0])])
        if cp.returncode != 0:
            report.fail("wheel.pip-install", (cp.stdout or "") + (cp.stderr or "") or f"exit={cp.returncode}")
            return

        print("  运行 wheel 态断言（version + entrypoints）...")
        verify_src = td / "verify_wheel.py"
        verify_src.write_text(
            """
import importlib.util
import os
import sys
import xianyu_mcp

print("  - xianyu_mcp.__version__ =", xianyu_mcp.__version__)
assert xianyu_mcp.__version__ == "1.0.0", f"wheel 安装态 __version__ 必须是 1.0.0，实际 {xianyu_mcp.__version__!r}"

vb = os.path.dirname(sys.executable)
new_ep = os.path.join(vb, "xianyu-mcp-server")
old_ep = os.path.join(vb, "xianyu-mcp")
assert os.path.exists(new_ep), f"新入口点 xianyu-mcp-server 不存在，未注册？路径: {new_ep}"
assert not os.path.exists(old_ep), f"旧入口点 xianyu-mcp 仍存在，scripts 未清理干净？路径: {old_ep}"

# 还检查包元数据：Distribution.name 必须是 'xianyu-mcp-server'
if importlib.util.find_spec("importlib.metadata"):
    from importlib.metadata import distribution
    d = distribution("xianyu-mcp-server")
    assert d.metadata["Name"] == "xianyu-mcp-server", d.metadata["Name"]
    print("  - Distribution Name =", d.metadata["Name"])
    print("  - Distribution Version =", d.metadata["Version"])
    assert d.metadata["Version"] == "1.0.0", d.metadata["Version"]
print("  OK")
""".strip()
            + "\n"
        )
        cp = run([str(venv_py), str(verify_src)], capture=True)
        print(cp.stdout or "", end="")
        if cp.returncode == 0:
            report.ok("wheel.install-smoke", "version=1.0.0，仅新入口点存在，Distribution 元数据正确")
        else:
            err = (cp.stderr or cp.stdout or "").strip() or f"exit={cp.returncode}"
            report.fail("wheel.install-smoke", err)


def main() -> int:
    _python_ok = sys.version_info >= (3, 11)
    if not _python_ok:
        print(f"⚠️ 运行的 Python {sys.version_info} < 3.11，部分 tomllib / venv 特性可能缺失", file=sys.stderr)
    if not (REPO_ROOT / "pyproject.toml").exists() or not (PYXIANYU_ROOT / "pyproject.toml").exists():
        print("❌ 请在 xianyu-mcp-server 仓库根目录运行此脚本（且 third_party/pyxianyu submodule 已拉取）", file=sys.stderr)
        return 2

    report = Report()
    check_pyproject(report)
    check_compileall(report)
    check_unittests(report)
    check_wheel_install(report)

    print("\n" + "=" * 64)
    print(f"汇总：通过 {len(report.passed)} / 失败 {len(report.failed)}")
    if report.failed:
        print("失败项：", [n for n, _ in report.failed], file=sys.stderr)
        print("\n建议：根据上面 ❌ 明细逐个修复后，重新运行本脚本再打 tag。", file=sys.stderr)
        return 1
    print("🎉 发布前自检全部通过，可以执行：")
    print("   1. git tag -s v1.0.0 -m 'Release xianyu-mcp-server 1.0.0'")
    print("   2. git push origin v1.0.0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
