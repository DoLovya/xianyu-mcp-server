from __future__ import annotations

import json
import re
from typing import Any


def _extract_js_object(text: str, start: int) -> str:
    i = start
    n = len(text)

    while i < n and text[i] != "{":
        i += 1
    if i >= n:
        raise ValueError("未找到对象起始 {")

    depth = 0
    in_string = False
    string_quote = ""
    escaped = False
    j = i

    while j < n:
        ch = text[j]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == string_quote:
                in_string = False
                string_quote = ""
        else:
            if ch in {"\"", "'"}:
                in_string = True
                string_quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[i : j + 1]

        j += 1

    raise ValueError("未找到对象结束 }")


def extract_login_form_data(html: str) -> dict[str, Any]:
    positions = [m.start() for m in re.finditer(r"window\.viewData\s*=", html)]
    if not positions:
        raise ValueError("未找到 window.viewData")

    for pos in reversed(positions):
        eq = html.find("=", pos)
        if eq < 0:
            continue
        try:
            obj = _extract_js_object(html, eq)
            view_data = json.loads(obj)
        except Exception:
            continue

        data = view_data.get("loginFormData")
        if not isinstance(data, dict):
            continue
        data = dict(data)
        data["umidTag"] = "SERVER"
        return data

    raise ValueError("未找到 loginFormData")


def extract_htoken(html: str) -> str:
    match = re.search(r"htoken=([A-Za-z0-9_\-]+)", html)
    if not match:
        raise ValueError("未能提取 htoken")
    return match.group(1)


def extract_verify_modes_url(html: str) -> str:
    match = re.search(
        r"window\.location\.href\s*=\s*\"(https://[^\"]*?/iv/mini/verify_modes\.htm\?[^\"]*)\"",
        html,
    )
    if not match:
        raise ValueError("未能提取 verify_modes 链接")
    url = match.group(1)
    if url.endswith("_umidfg="):
        url += "1"
    return url


def extract_face_qr_content(html: str) -> str:
    match = re.search(r"new\s+Qrcode\(\{\s*text:\s*\"([^\"]+)\"", html)
    if not match:
        raise ValueError("未能提取人脸验证二维码内容")
    return match.group(1)
