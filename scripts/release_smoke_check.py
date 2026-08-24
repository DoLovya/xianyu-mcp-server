#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a built wheel into a clean venv and verify release metadata.")
    parser.add_argument("--wheel", required=True, help="Path to the wheel file to install.")
    parser.add_argument("--version", required=True, help="Expected package version, without the leading v.")
    return parser.parse_args()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    args = parse_args()
    wheel = Path(args.wheel).resolve()
    if not wheel.exists():
        raise SystemExit(f"Wheel not found: {wheel}")

    with tempfile.TemporaryDirectory(prefix="xianyu-mcp-smoke-") as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.create(str(venv_dir), with_pip=True, clear=True)
        py = venv_dir / "bin" / "python"
        if not py.exists():
            raise SystemExit(f"venv python not found: {py}")

        cp = run([str(py), "-m", "pip", "install", "--quiet", str(wheel)])
        if cp.returncode != 0:
            detail = (cp.stdout or "") + (cp.stderr or "")
            raise SystemExit(detail.strip() or f"pip install failed: exit={cp.returncode}")

        verify = f"""
import importlib.util
import os
import sys
import xianyu_mcp

expected = {args.version!r}
print("  - xianyu_mcp.__version__ =", xianyu_mcp.__version__)
assert xianyu_mcp.__version__ == expected, f"wheel __version__ mismatch: {{xianyu_mcp.__version__!r}} vs {{expected!r}}"

vb = os.path.dirname(sys.executable)
new_ep = os.path.join(vb, "xianyu-mcp-server")
old_ep = os.path.join(vb, "xianyu-mcp")
assert os.path.exists(new_ep), f"entrypoint missing: {{new_ep}}"
assert not os.path.exists(old_ep), f"legacy entrypoint still exists: {{old_ep}}"

if importlib.util.find_spec("importlib.metadata"):
    from importlib.metadata import distribution
    d = distribution("xianyu-mcp-server")
    assert d.metadata["Name"] == "xianyu-mcp-server", d.metadata["Name"]
    assert d.metadata["Version"] == expected, d.metadata["Version"]
    print("  - Distribution Name =", d.metadata["Name"])
    print("  - Distribution Version =", d.metadata["Version"])

print("  OK")
"""
        cp = run([str(py), "-c", verify])
        if cp.stdout:
            print(cp.stdout, end="")
        if cp.returncode != 0:
            detail = (cp.stderr or "") + (cp.stdout or "")
            raise SystemExit(detail.strip() or f"wheel verification failed: exit={cp.returncode}")

    print("wheel install smoke: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
