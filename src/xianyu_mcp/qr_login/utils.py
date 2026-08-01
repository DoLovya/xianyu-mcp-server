from __future__ import annotations

import base64
import json
from io import BytesIO
from typing import Any

import qrcode
import qrcode.constants


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def cookies_dict_to_str(cookies: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def render_qr_data_url(content: str) -> str:
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(content)
    qr.make()
    img = qr.make_image()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"
