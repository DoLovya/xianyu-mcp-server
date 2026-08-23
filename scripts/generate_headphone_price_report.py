from __future__ import annotations

import argparse
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from xianyu_mcp.reports.headphone_price_report import generate_headphone_price_report
from xianyu_mcp.server import _load_cookie_str
from xianyu_mcp.tools.xianyu_api_tools import XianYuApiTools


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/headphone_price_report.html")
    parser.add_argument("--max-own-items", type=int, default=10)
    parser.add_argument("--samples-per-item", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=0.10)
    args = parser.parse_args()

    tools = XianYuApiTools(_load_cookie_str())
    result = generate_headphone_price_report(
        tools,
        output_path=args.output,
        max_own_items=args.max_own_items,
        samples_per_item=args.samples_per_item,
        threshold=args.threshold,
    )
    sys.stdout.write(str(result.get("report_path") or result.get("output_path") or "") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
