import json

from xianyu_mcp.server import _load_cookie_str
from xianyu_mcp.tools.xianyu_api_tools import XianYuApiTools


def main() -> None:
    kw = "漫步者 W830NB 头戴式 蓝牙 耳机"
    api = XianYuApiTools(cookie_str=_load_cookie_str())
    res = json.loads(api.search_items(kw, page_number=1, rows_per_page=1))
    raw = res.get("raw") or {}
    entry = ((raw.get("data") or {}).get("resultList") or [{}])[0]
    data = entry.get("data") or {}

    item_ex = (((data.get("item") or {}).get("main") or {}).get("exContent") or {})
    seller_ex = (((data.get("seller") or {}).get("main") or {}).get("exContent") or {})
    trade_ex = (((data.get("trade") or {}).get("main") or {}).get("exContent") or {})

    print("data_keys:", sorted(data.keys()))
    print("item_ex_keys:", sorted(item_ex.keys())[:60])
    print(
        "item_ex_sample:",
        {k: item_ex.get(k) for k in ["itemId", "title", "price", "soldQuantity", "itemDegree", "publishTime"]},
    )
    print("seller_ex_keys:", sorted(seller_ex.keys())[:80])
    print(
        "seller_ex_sample:",
        {k: seller_ex.get(k) for k in ["userId", "userNickName", "creditLevel", "creditScore", "goodRate", "zhimaLevel"]},
    )
    print("trade_ex_keys:", sorted(trade_ex.keys())[:80])
    print("trade_ex_sample:", {k: trade_ex.get(k) for k in ["soldQuantity", "tradeCount", "wantCount"]})


if __name__ == "__main__":
    main()
