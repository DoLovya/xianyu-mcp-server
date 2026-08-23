from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from xianyu_mcp.server import edit_item, get_item_detail, get_item_edit_detail


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


def _extract_title_and_price_cent(edit_detail: dict[str, Any]) -> tuple[str, int | None]:
    detail = edit_detail.get("data") if isinstance(edit_detail.get("data"), dict) else edit_detail

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

    if price_cent is None and detail.get("defaultPrice") is not None:
        try:
            price_cent = int(str(detail.get("defaultPrice")).strip())
        except Exception:
            price_cent = None

    return title, price_cent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--new-price", required=True)
    parser.add_argument("--title-suffix", default=" (mcp-test)")
    parser.add_argument("--artifacts-dir", default="artifacts")
    args = parser.parse_args()

    item_id = str(args.item_id).strip()
    if not item_id:
        raise ValueError("item_id 不能为空。")

    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("[1/7] get_item_edit_detail (before)")
    raw_edit_detail_before = get_item_edit_detail(item_id)
    (artifacts_dir / f"edit_detail_before_{item_id}.json").write_text(
        raw_edit_detail_before, encoding="utf-8"
    )
    edit_detail_before = _safe_json_load(raw_edit_detail_before) or {}
    orig_title, orig_price_cent = _extract_title_and_price_cent(edit_detail_before)
    if not orig_title:
        raise RuntimeError("未能从 edit_detail 提取原标题（itemTextDTO.title）。")
    if orig_price_cent is None:
        raise RuntimeError("未能从 edit_detail 提取原价（itemPriceDTO.priceInCent / defaultPrice）。")

    orig_price_yuan = f"{orig_price_cent / 100:.2f}"
    suffix = str(args.title_suffix)
    new_title = orig_title + suffix if not orig_title.endswith(suffix) else orig_title

    print("- item_id:", item_id)
    print("- orig_title:", orig_title)
    print("- orig_price_yuan:", orig_price_yuan)
    print("- new_title:", new_title)
    print("- new_price_yuan:", str(args.new_price))

    print("\n[2/7] edit_item apply (overrides)")
    raw_apply = edit_item(item_id, overrides={"title": new_title, "price": str(args.new_price)})
    (artifacts_dir / f"edit_item_apply_{item_id}.json").write_text(raw_apply, encoding="utf-8")
    apply_obj = _safe_json_load(raw_apply) or {}
    print("- apply_success:", apply_obj.get("success"))
    print("- apply_api:", apply_obj.get("api"))

    print("\n[3/7] get_item_edit_detail (after apply)")
    raw_edit_detail_after_apply = get_item_edit_detail(item_id)
    (artifacts_dir / f"edit_detail_after_apply_{item_id}.json").write_text(
        raw_edit_detail_after_apply, encoding="utf-8"
    )
    edit_detail_after_apply_obj = _safe_json_load(raw_edit_detail_after_apply) or {}
    after_apply_title_from_edit, after_apply_price_cent = _extract_title_and_price_cent(
        edit_detail_after_apply_obj
    )
    print("- title_after_apply(edit_detail):", after_apply_title_from_edit)
    print("- price_after_apply_cent(edit_detail):", after_apply_price_cent)

    print("\n[4/7] get_item_detail (after apply)")
    raw_detail_after_apply = get_item_detail(item_id)
    (artifacts_dir / f"item_detail_after_apply_{item_id}.json").write_text(
        raw_detail_after_apply, encoding="utf-8"
    )
    after_apply_obj = _safe_json_load(raw_detail_after_apply) or {}
    after_apply_title = (
        _find_first(after_apply_obj, ["data", "item", "title"])
        or _find_first(after_apply_obj, ["data", "itemDO", "title"])
        or ""
    )
    print("- title_after_apply:", after_apply_title)

    print("\n[5/7] edit_item rollback")
    raw_rollback = edit_item(item_id, overrides={"title": orig_title, "price": orig_price_yuan})
    (artifacts_dir / f"edit_item_rollback_{item_id}.json").write_text(raw_rollback, encoding="utf-8")
    rollback_obj = _safe_json_load(raw_rollback) or {}
    print("- rollback_success:", rollback_obj.get("success"))
    print("- rollback_api:", rollback_obj.get("api"))

    print("\n[6/7] get_item_edit_detail (after rollback)")
    raw_edit_detail_after_rollback = get_item_edit_detail(item_id)
    (artifacts_dir / f"edit_detail_after_rollback_{item_id}.json").write_text(
        raw_edit_detail_after_rollback, encoding="utf-8"
    )
    edit_detail_after_rollback_obj = _safe_json_load(raw_edit_detail_after_rollback) or {}
    after_rollback_title_from_edit, after_rollback_price_cent = _extract_title_and_price_cent(
        edit_detail_after_rollback_obj
    )
    print("- title_after_rollback(edit_detail):", after_rollback_title_from_edit)
    print("- price_after_rollback_cent(edit_detail):", after_rollback_price_cent)

    print("\n[7/7] get_item_detail (after rollback)")
    raw_detail_after_rollback = get_item_detail(item_id)
    (artifacts_dir / f"item_detail_after_rollback_{item_id}.json").write_text(
        raw_detail_after_rollback, encoding="utf-8"
    )
    after_rollback_obj = _safe_json_load(raw_detail_after_rollback) or {}
    after_rollback_title = (
        _find_first(after_rollback_obj, ["data", "item", "title"])
        or _find_first(after_rollback_obj, ["data", "itemDO", "title"])
        or ""
    )
    print("- title_after_rollback:", after_rollback_title)
    print("\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
