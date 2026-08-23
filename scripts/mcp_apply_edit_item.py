from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _safe_json_load(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return None


def _find_first(data: Any, keys: list[str]) -> Any:
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _extract_title_from_item_detail(detail_obj: dict[str, Any]) -> str:
    return str(
        _find_first(detail_obj, ["data", "item", "title"])
        or _find_first(detail_obj, ["data", "itemDO", "title"])
        or ""
    )


def _extract_title_price_cent_from_edit_detail(edit_obj: dict[str, Any]) -> tuple[str, int | None]:
    detail = edit_obj.get("data") if isinstance(edit_obj.get("data"), dict) else edit_obj
    title = ""
    item_text = detail.get("itemTextDTO")
    if isinstance(item_text, dict):
        title = str(item_text.get("title") or "")
    price_cent = None
    item_price = detail.get("itemPriceDTO")
    if isinstance(item_price, dict) and item_price.get("priceInCent") is not None:
        try:
            price_cent = int(str(item_price.get("priceInCent")).strip())
        except Exception:
            price_cent = None
    return title, price_cent


def _extract_text_payload(result) -> str:
    content = getattr(result, "content", None) or []
    for item in content:
        if getattr(item, "type", None) == "text":
            return getattr(item, "text", "")
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and isinstance(structured.get("result"), str):
        return structured["result"]
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False, indent=2)
    return ""


async def _run(args: argparse.Namespace) -> None:
    repo_root = Path.cwd()
    artifacts_dir = repo_root / "artifacts" / "mcp_apply_edit_item"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    server = StdioServerParameters(
        command=str(repo_root / ".venv" / "bin" / "python"),
        args=["-m", "xianyu_mcp.server"],
        env={"PYTHONPATH": "src"},
        cwd=str(repo_root),
    )

    item_id = str(args.item_id).strip()
    new_price = str(args.price).strip()
    title_suffix = str(args.title_suffix)

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            before_detail_res = await session.call_tool("get_item_detail", {"item_id": item_id})
            before_detail_text = _extract_text_payload(before_detail_res)
            (artifacts_dir / f"item_detail_before_{item_id}.json").write_text(
                before_detail_text, encoding="utf-8"
            )
            before_detail_obj = _safe_json_load(before_detail_text) or {}
            before_title = _extract_title_from_item_detail(before_detail_obj)

            base_title = before_title
            if not base_title:
                before_edit_res = await session.call_tool("get_item_edit_detail", {"item_id": item_id})
                before_edit_text = _extract_text_payload(before_edit_res)
                (artifacts_dir / f"edit_detail_before_{item_id}.json").write_text(
                    before_edit_text, encoding="utf-8"
                )
                before_edit_obj = _safe_json_load(before_edit_text) or {}
                base_title, _ = _extract_title_price_cent_from_edit_detail(before_edit_obj)

            if not base_title:
                raise RuntimeError("Cannot parse original title from server response")

            new_title = base_title if base_title.endswith(title_suffix) else (base_title + title_suffix)

            apply_res = await session.call_tool(
                "edit_item",
                {
                    "item_id": item_id,
                    "overrides": {"title": new_title, "price": new_price},
                },
            )
            apply_text = _extract_text_payload(apply_res)
            (artifacts_dir / f"edit_item_apply_{item_id}.json").write_text(apply_text, encoding="utf-8")
            apply_obj = _safe_json_load(apply_text) or {}

            after_edit_res = await session.call_tool("get_item_edit_detail", {"item_id": item_id})
            after_edit_text = _extract_text_payload(after_edit_res)
            (artifacts_dir / f"edit_detail_after_{item_id}.json").write_text(after_edit_text, encoding="utf-8")
            after_edit_obj = _safe_json_load(after_edit_text) or {}
            after_edit_title, after_price_cent = _extract_title_price_cent_from_edit_detail(after_edit_obj)

            after_detail_res = await session.call_tool("get_item_detail", {"item_id": item_id})
            after_detail_text = _extract_text_payload(after_detail_res)
            (artifacts_dir / f"item_detail_after_{item_id}.json").write_text(
                after_detail_text, encoding="utf-8"
            )
            after_detail_obj = _safe_json_load(after_detail_text) or {}
            after_title = _extract_title_from_item_detail(after_detail_obj)

            print("MCP tool call finished")
            print("item_id:", item_id)
            print("before_title(detail):", before_title)
            print("requested_title:", new_title)
            print("requested_price_yuan:", new_price)
            print("apply_success:", apply_obj.get("success"))
            print("apply_api:", apply_obj.get("api"))
            print("after_title(detail):", after_title)
            print("after_title(edit_detail):", after_edit_title)
            print("after_price_cent(edit_detail):", after_price_cent)
            print("artifacts_dir:", str(artifacts_dir))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--price", required=True)
    parser.add_argument("--title-suffix", default="(mcp修改)")
    args = parser.parse_args()
    anyio.run(_run, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
