import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from xianyu_mcp.server import _load_cookie_str
from xianyu_mcp.tools.xianyu_api_tools import XianYuApiTools


def _safe_int(v: Any) -> int | None:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def _parse_price_to_float(price_text: str) -> float | None:
    text = str(price_text or "").strip()
    if not text:
        return None
    text = text.replace("¥", "").replace(",", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _extract_specs(detail_data: dict[str, Any]) -> dict[str, str]:
    item = (detail_data.get("itemDO") or {}) if isinstance(detail_data.get("itemDO"), dict) else {}
    label_ext_list = item.get("itemLabelExtList") or []
    specs: dict[str, str] = {}
    if isinstance(label_ext_list, list):
        for entry in label_ext_list:
            if not isinstance(entry, dict):
                continue
            k = str(entry.get("propertyText") or "").strip()
            v = str(entry.get("valueText") or entry.get("text") or "").strip()
            if k and v:
                specs[k] = v
    return specs


def _extract_images(detail_data: dict[str, Any]) -> list[str]:
    item = (detail_data.get("itemDO") or {}) if isinstance(detail_data.get("itemDO"), dict) else {}
    image_infos = item.get("imageInfos") or []
    urls: list[str] = []
    if isinstance(image_infos, list):
        for img in image_infos:
            if isinstance(img, dict) and img.get("url"):
                urls.append(str(img.get("url")))
    return urls


def _extract_publish_time(detail_data: dict[str, Any]) -> str:
    item = (detail_data.get("itemDO") or {}) if isinstance(detail_data.get("itemDO"), dict) else {}
    ts = item.get("gmtCreate")
    if isinstance(ts, (int, float)) and ts > 0:
        try:
            return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    text = str(item.get("GMT_CREATE_DATE_KEY") or "").strip()
    return text


def _extract_model_from_title(title: str) -> str:
    t = str(title or "")
    candidates = re.findall(r"[A-Za-z]{1,6}\d{2,6}[A-Za-z]{0,6}", t)
    for c in candidates:
        if 4 <= len(c) <= 12:
            return c.upper()
    return ""


def _build_search_keyword(title: str, specs: dict[str, str]) -> str:
    model = _extract_model_from_title(title)
    brand = specs.get("品牌") or ""
    brand_cn = ""
    if "漫步者" in brand:
        brand_cn = "漫步者"
    parts = [p for p in [brand_cn, model, "耳机"] if p]
    kw = " ".join(parts).strip()
    return kw or (str(title).strip() + " 耳机")


def _is_valid_competitor_title(title: str, model: str) -> bool:
    t = str(title or "").lower()
    if "耳机" not in t:
        return False
    bad = [
        "收纳",
        "收纳盒",
        "耳机包",
        "耳套",
        "耳罩",
        "海绵",
        "保护",
        "配件",
        "线",
        "壳",
        "套",
        "替换",
        "维修",
    ]
    if any(b in t for b in bad):
        return False
    if model and model.lower() not in t:
        return False
    return True


def _choose_bin_size(min_p: float, max_p: float) -> float:
    r = max_p - min_p
    if r <= 50:
        return 5
    if r <= 100:
        return 10
    if r <= 200:
        return 20
    if r <= 500:
        return 50
    return 100


def _make_bins(prices: list[float]) -> tuple[list[float], list[str], list[int]]:
    if not prices:
        return [], [], []
    mn = min(prices)
    mx = max(prices)
    step = _choose_bin_size(mn, mx)
    start = math.floor(mn / step) * step
    end = math.ceil(mx / step) * step
    edges: list[float] = []
    x = start
    while x < end + 1e-9:
        edges.append(round(x, 2))
        x += step
    labels: list[str] = []
    counts = [0 for _ in range(max(0, len(edges) - 1))]
    for i in range(len(edges) - 1):
        labels.append(f"{edges[i]:g}-{edges[i+1]:g}")
    for p in prices:
        idx = int((p - start) // step)
        if idx < 0:
            continue
        if idx >= len(counts):
            idx = len(counts) - 1
        counts[idx] += 1
    return edges, labels, counts


@dataclass(frozen=True)
class MyItem:
    item_id: str
    title: str
    price: float | None
    publish_time: str
    images: list[str]
    specs: dict[str, str]
    keyword: str
    model: str


def _load_json(text: str) -> dict[str, Any]:
    return json.loads(text)


def _generate_html(report: dict[str, Any], out_path: Path) -> None:
    data_json = json.dumps(report, ensure_ascii=False)
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>闲鱼耳机竞品价格对比报告</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0b0f17;
      --panel: #111827;
      --muted: #94a3b8;
      --text: #e5e7eb;
      --accent: #60a5fa;
      --border: rgba(148,163,184,0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, \"PingFang SC\", \"Noto Sans CJK SC\", \"Microsoft YaHei\", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      padding: 20px 16px;
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      background: rgba(11,15,23,0.85);
      backdrop-filter: blur(8px);
      z-index: 10;
    }}
    header h1 {{
      font-size: 18px;
      margin: 0;
    }}
    header .meta {{
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
    }}
    main {{
      padding: 16px;
      display: grid;
      gap: 14px;
      max-width: 1100px;
      margin: 0 auto;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
    }}
    .card h2 {{
      font-size: 16px;
      margin: 0 0 10px 0;
    }}
    .grid {{
      display: grid;
      gap: 12px;
      grid-template-columns: 320px 1fr;
    }}
    .kv {{
      display: grid;
      gap: 6px;
      font-size: 13px;
      color: var(--muted);
    }}
    .kv b {{
      color: var(--text);
      font-weight: 600;
    }}
    .thumbs {{
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(3, 1fr);
    }}
    .thumbs img {{
      width: 100%;
      aspect-ratio: 3 / 4;
      object-fit: cover;
      border-radius: 10px;
      border: 1px solid var(--border);
      cursor: zoom-in;
      background: rgba(148,163,184,0.05);
    }}
    .plot {{
      width: 100%;
      height: 360px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 8px 6px;
      vertical-align: top;
    }}
    th {{
      text-align: left;
      color: var(--muted);
      font-weight: 600;
      position: sticky;
      top: 0;
      background: var(--panel);
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
    }}
    .good {{ color: #34d399; }}
    .warn {{ color: #fbbf24; }}
    .bad {{ color: #fb7185; }}
    .modal {{
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      z-index: 999;
    }}
    .modal.open {{ display: flex; }}
    .modal img {{
      max-width: min(1100px, 96vw);
      max-height: 90vh;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: #000;
      transform-origin: center center;
    }}
    .modal .toolbar {{
      position: absolute;
      top: 12px;
      right: 12px;
      display: flex;
      gap: 8px;
    }}
    .btn {{
      padding: 6px 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: rgba(17,24,39,0.9);
      color: var(--text);
      cursor: pointer;
      font-size: 12px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>闲鱼耳机竞品价格对比报告</h1>
    <div class="meta" id="meta"></div>
  </header>
  <main id="root"></main>

  <div class="modal" id="imgModal">
    <div class="toolbar">
      <button class="btn" id="zoomOut">-</button>
      <button class="btn" id="zoomIn">+</button>
      <button class="btn" id="zoomReset">100%</button>
      <button class="btn" id="zoomClose">关闭</button>
    </div>
    <img id="modalImg" alt="" />
  </div>

  <script>
    const REPORT = __REPORT_JSON__;

    const fmt = (n) => (n === null || n === undefined || Number.isNaN(n)) ? '-' : (Math.round(n * 100) / 100).toString();
    const fmtMoney = (n) => (n === null || n === undefined || Number.isNaN(n)) ? '-' : ('¥' + fmt(n));

    const meta = document.getElementById('meta');
    meta.textContent = `生成时间：${REPORT.generated_at} ｜ 我的耳机商品数：${REPORT.my_items.length} ｜ 竞品总条数：${REPORT.total_competitors}`;

    const root = document.getElementById('root');

    function mk(tag, attrs, children) {{
      const el = document.createElement(tag);
      if (attrs) {{
        for (const [k, v] of Object.entries(attrs)) {{
          if (k === 'class') el.className = v;
          else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
          else el.setAttribute(k, v);
        }}
      }}
      if (children) {{
        for (const c of children) {{
          if (c === null || c === undefined) continue;
          if (typeof c === 'string') el.appendChild(document.createTextNode(c));
          else el.appendChild(c);
        }}
      }}
      return el;
    }}

    const modal = document.getElementById('imgModal');
    const modalImg = document.getElementById('modalImg');
    let zoom = 1;
    const applyZoom = () => {{
      modalImg.style.transform = `scale(${zoom})`;
    }};
    const openImg = (src) => {{
      zoom = 1;
      applyZoom();
      modalImg.src = src;
      modal.classList.add('open');
    }};
    const closeImg = () => {{
      modal.classList.remove('open');
      modalImg.src = '';
    }};
    document.getElementById('zoomIn').addEventListener('click', () => {{ zoom = Math.min(5, zoom + 0.25); applyZoom(); }});
    document.getElementById('zoomOut').addEventListener('click', () => {{ zoom = Math.max(0.5, zoom - 0.25); applyZoom(); }});
    document.getElementById('zoomReset').addEventListener('click', () => {{ zoom = 1; applyZoom(); }});
    document.getElementById('zoomClose').addEventListener('click', closeImg);
    modal.addEventListener('click', (e) => {{ if (e.target === modal) closeImg(); }});
    window.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') closeImg(); }});

    function renderItemCard(item) {{
      const specs = Object.entries(item.specs || {{}}).slice(0, 12).map(([k, v]) => `${k}：${v}`).join(' ｜ ');
      const verdict = item.analysis?.verdict || '未知';
      const verdictClass = verdict.includes('偏低') ? 'good' : (verdict.includes('偏高') ? 'bad' : 'warn');

      const left = mk('div', null, [
        mk('div', {{ class: 'kv' }}, [
          mk('div', null, [mk('b', null, ['商品 ID：']), item.item_id]),
          mk('div', null, [mk('b', null, ['发布价：']), fmtMoney(item.my_price)]),
          mk('div', null, [mk('b', null, ['上架时间：']), item.publish_time || '-']),
          mk('div', null, [mk('b', null, ['搜索关键词：']), item.keyword]),
          mk('div', null, [mk('b', null, ['规格参数：']), specs || '-']),
          mk('div', null, [mk('b', null, ['结论：']), mk('span', {{ class: verdictClass }}, [verdict])]),
          mk('div', null, [mk('span', {{ class: 'badge' }}, [`竞品条数：${item.competitors.length}`])]),
        ])
      ]);

      const imgs = mk('div', {{ class: 'thumbs' }}, (item.images || []).slice(0, 6).map((u) =>
        mk('img', {{ src: u, alt: item.title, onclick: () => openImg(u) }}, null)
      ));

      const plot1 = mk('div', {{ class: 'plot', id: `hist_${item.item_id}` }}, null);
      const plot2 = mk('div', {{ class: 'plot', id: `bar_${item.item_id}` }}, null);

      const table = mk('table', null, [
        mk('thead', null, [mk('tr', null, [
          mk('th', null, ['#']),
          mk('th', null, ['标题']),
          mk('th', null, ['价格']),
          mk('th', null, ['成色']),
          mk('th', null, ['卖家指标']),
          mk('th', null, ['卖家卖出']),
          mk('th', null, ['地区']),
        ])]),
        mk('tbody', null, item.competitors.map((c, idx) =>
          mk('tr', null, [
            mk('td', null, [String(idx + 1)]),
            mk('td', null, [c.title || '-']),
            mk('td', null, [fmtMoney(c.price)]),
            mk('td', null, [c.condition || '-']),
            mk('td', null, [c.seller_credit_text || '-']),
            mk('td', null, [c.seller_sold_text || '-']),
            mk('td', null, [c.area || '-']),
          ])
        ))
      ]);

      const container = mk('div', {{ class: 'card' }}, [
        mk('h2', null, [item.title]),
        mk('div', {{ class: 'grid' }}, [
          mk('div', null, [left, mk('div', {{ style: 'height: 10px' }}, null), imgs]),
          mk('div', null, [
            plot1,
            mk('div', {{ style: 'height: 12px' }}, null),
            plot2,
            mk('div', {{ style: 'height: 12px' }}, null),
            mk('div', {{ class: 'card' }}, [mk('h2', null, ['竞品明细（Top 30）']), table]),
          ])
        ])
      ]);

      setTimeout(() => {{
        const prices = item.competitors.map(x => x.price).filter(x => typeof x === 'number');
        const labels = item.competitors.map((_, i) => `#${i + 1}`);

        Plotly.newPlot(`hist_${item.item_id}`, [
          {{
            x: prices,
            type: 'histogram',
            marker: {{ color: '#60a5fa' }},
            nbinsx: item.analysis?.bin_labels?.length || undefined
          }}
        ], {{
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          margin: {{ l: 40, r: 10, t: 24, b: 40 }},
          title: {{ text: '竞品价格分布（直方图，可缩放）', font: {{ size: 12, color: '#e5e7eb' }} }},
          xaxis: {{ title: '价格', color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.15)' }},
          yaxis: {{ title: '数量', color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.15)' }},
          shapes: item.my_price ? [{{
            type: 'line',
            x0: item.my_price, x1: item.my_price,
            y0: 0, y1: 1,
            yref: 'paper',
            line: {{ color: '#fb7185', width: 2, dash: 'dash' }}
          }}] : []
        }}, {{ responsive: true }});

        Plotly.newPlot(`bar_${item.item_id}`, [
          {{
            x: labels,
            y: prices,
            type: 'bar',
            marker: {{ color: '#34d399' }},
            name: '竞品价格'
          }}
        ], {{
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          margin: {{ l: 40, r: 10, t: 24, b: 80 }},
          title: {{ text: '竞品价格对比（柱状图，可缩放）', font: {{ size: 12, color: '#e5e7eb' }} }},
          xaxis: {{ color: '#94a3b8', tickangle: -45, gridcolor: 'rgba(148,163,184,0.15)' }},
          yaxis: {{ title: '价格', color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.15)' }},
          shapes: item.my_price ? [{{
            type: 'line',
            x0: -0.5, x1: prices.length - 0.5,
            y0: item.my_price, y1: item.my_price,
            xref: 'x', yref: 'y',
            line: {{ color: '#fb7185', width: 2, dash: 'dash' }}
          }}] : []
        }}, {{ responsive: true }});
      }}, 0);

      return container;
    }}

    const heat = mk('div', {{ class: 'card' }}, [
      mk('h2', null, ['同品类价格区间热力图']),
      mk('div', {{ class: 'plot', id: 'heatmap' }}, null),
    ]);
    root.appendChild(heat);

    const heatRows = REPORT.heatmap?.rows || [];
    const heatCols = REPORT.heatmap?.cols || [];
    const heatZ = REPORT.heatmap?.z || [];
    Plotly.newPlot('heatmap', [
      {{
        z: heatZ,
        x: heatCols,
        y: heatRows,
        type: 'heatmap',
        colorscale: 'Blues'
      }}
    ], {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      margin: {{ l: 110, r: 10, t: 10, b: 60 }},
      xaxis: {{ color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.15)' }},
      yaxis: {{ color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.15)' }},
    }}, {{ responsive: true }});

    for (const item of REPORT.my_items) {{
      root.appendChild(renderItemCard(item));
    }}
  </script>
</body>
</html>
"""
    template = html.replace("{{", "{").replace("}}", "}")
    out_path.write_text(template.replace("__REPORT_JSON__", data_json), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-competitors", type=int, default=30)
    parser.add_argument("--rows-per-page", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--out", type=str, default="artifacts/headphone_competitor_report.html")
    args = parser.parse_args()

    api = XianYuApiTools(cookie_str=_load_cookie_str())

    my_items_raw = _load_json(api.list_my_items(page_size=20))
    cards = my_items_raw.get("items") or []
    my_item_ids = []
    for c in cards:
        if isinstance(c, dict) and c.get("item_id"):
            my_item_ids.append(str(c.get("item_id")))

    my_headphones: list[MyItem] = []
    for item_id in my_item_ids:
        detail = _load_json(api.get_item_detail(item_id))
        data = detail.get("data") or {}
        item_do = data.get("itemDO") or {}
        title = str(item_do.get("title") or "").strip()
        if "耳机" not in title:
            continue
        specs = _extract_specs(data)
        imgs = _extract_images(data)
        publish_time = _extract_publish_time(data)
        sold_price = _parse_price_to_float(str(item_do.get("soldPrice") or item_do.get("soldPrice") or ""))
        keyword = _build_search_keyword(title, specs)
        model = _extract_model_from_title(title)
        my_headphones.append(
            MyItem(
                item_id=item_id,
                title=title,
                price=sold_price,
                publish_time=publish_time,
                images=imgs,
                specs=specs,
                keyword=keyword,
                model=model,
            )
        )

    uniq: dict[str, MyItem] = {}
    for it in my_headphones:
        key = it.model or it.title
        if key not in uniq:
            uniq[key] = it

    my_headphones = list(uniq.values())

    report_items: list[dict[str, Any]] = []
    all_heat_cols: list[str] = []
    heat_rows: list[str] = []
    heat_matrix: list[list[int]] = []
    total_competitors = 0

    for my_item in my_headphones:
        model = my_item.model
        competitor_candidates: list[dict[str, Any]] = []
        seen: set[str] = set()

        for page in range(1, args.max_pages + 1):
            search = _load_json(
                api.search_items(
                    my_item.keyword,
                    page_number=page,
                    rows_per_page=args.rows_per_page,
                    sort_field="create",
                    sort_value="desc",
                )
            )
            for entry in search.get("items") or []:
                if not isinstance(entry, dict):
                    continue
                cid = str(entry.get("item_id") or "").strip()
                if not cid or cid in seen or cid in my_item_ids:
                    continue
                title = str(entry.get("title") or "")
                if not _is_valid_competitor_title(title, model):
                    continue
                price = _parse_price_to_float(str(entry.get("price") or ""))
                if price is None or price <= 0:
                    continue
                seen.add(cid)
                competitor_candidates.append(
                    {
                        "item_id": cid,
                        "title": title,
                        "price": price,
                        "pic_url": entry.get("pic_url") or "",
                        "area": entry.get("area") or "",
                        "user_nick_name": entry.get("user_nick_name") or "",
                    }
                )
            if len(competitor_candidates) >= args.min_competitors:
                break
            if not search.get("has_next_page"):
                break

        competitors: list[dict[str, Any]] = []
        for c in competitor_candidates[: args.min_competitors]:
            cid = c["item_id"]
            detail = _load_json(api.get_item_detail(cid))
            data = detail.get("data") or {}
            item_do = data.get("itemDO") or {}
            seller_do = data.get("sellerDO") or {}
            specs = _extract_specs(data)

            seller_credit_score = seller_do.get("sellerCreditScore")
            if seller_credit_score is None:
                seller_credit_score = seller_do.get("creditScore")
            credit_text = ""
            if seller_credit_score is not None:
                credit_text = f"信誉分 {seller_credit_score}"
            else:
                reg = _safe_int(seller_do.get("userRegDay"))
                zhima = seller_do.get("zhimaAuth")
                parts = []
                if reg is not None:
                    parts.append(f"注册{reg}天")
                if isinstance(zhima, bool):
                    parts.append("芝麻认证" if zhima else "未芝麻认证")
                credit_text = " / ".join(parts) or "-"

            sold_num = seller_do.get("hasSoldNumInteger")
            sold_cnt = item_do.get("soldCnt")
            seller_sold_text = ""
            if sold_num is not None:
                seller_sold_text = f"{sold_num}"
            if sold_cnt is not None:
                seller_sold_text = (seller_sold_text + f" / 本宝贝售出{sold_cnt}").strip(" /")

            competitors.append(
                {
                    "item_id": cid,
                    "title": str(item_do.get("title") or c.get("title") or ""),
                    "price": _parse_price_to_float(str(item_do.get("soldPrice") or c.get("price") or "")) or c.get("price"),
                    "condition": specs.get("成色") or "",
                    "area": str(seller_do.get("publishCity") or c.get("area") or ""),
                    "seller_credit_score": seller_credit_score,
                    "seller_credit_text": credit_text,
                    "seller_sold_num": sold_num,
                    "seller_sold_text": seller_sold_text or "-",
                    "sold_cnt": sold_cnt,
                    "pic_url": c.get("pic_url") or "",
                }
            )

        prices = [c["price"] for c in competitors if isinstance(c.get("price"), (int, float))]
        prices = [float(p) for p in prices if p > 0]
        avg = mean(prices) if prices else None
        med = median(prices) if prices else None
        mn = min(prices) if prices else None
        mx = max(prices) if prices else None
        _, bin_labels, bin_counts = _make_bins(prices)

        verdict = "未知"
        if my_item.price is not None and med is not None and med > 0:
            diff = (my_item.price - med) / med
            if diff <= -0.1:
                verdict = f"偏低（低于中位数 {abs(diff)*100:.1f}%）"
            elif diff >= 0.1:
                verdict = f"偏高（高于中位数 {abs(diff)*100:.1f}%）"
            else:
                verdict = f"合理（接近中位数，差异 {abs(diff)*100:.1f}%）"

        report_items.append(
            {
                "item_id": my_item.item_id,
                "title": my_item.title,
                "my_price": my_item.price,
                "publish_time": my_item.publish_time,
                "images": my_item.images,
                "specs": my_item.specs,
                "keyword": my_item.keyword,
                "model": my_item.model,
                "competitors": competitors,
                "analysis": {
                    "count": len(prices),
                    "avg": avg,
                    "median": med,
                    "min": mn,
                    "max": mx,
                    "bin_labels": bin_labels,
                    "bin_counts": bin_counts,
                    "verdict": verdict,
                },
            }
        )

        total_competitors += len(competitors)

        if not all_heat_cols and bin_labels:
            all_heat_cols = bin_labels
        heat_rows.append(my_item.model or my_item.title)
        if all_heat_cols:
            row_counts = [0 for _ in range(len(all_heat_cols))]
            if bin_labels == all_heat_cols:
                row_counts = bin_counts
            heat_matrix.append(row_counts)

    report: dict[str, Any] = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "my_items": report_items,
        "total_competitors": total_competitors,
        "heatmap": {"rows": heat_rows, "cols": all_heat_cols, "z": heat_matrix},
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _generate_html(report, out_path)
    (out_path.with_suffix(".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(str(out_path))


if __name__ == "__main__":
    main()
