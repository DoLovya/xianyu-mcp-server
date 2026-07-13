from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import requests

_REPO_ROOT = Path(__file__).resolve().parents[3]
_XIANYU_APIS_ROOT = _REPO_ROOT / "third_party" / "XianYuApis"

_IMPORT_CACHE: dict[str, Any] | None = None


def _load_xianyu_modules() -> dict[str, Any]:
    global _IMPORT_CACHE
    if _IMPORT_CACHE is not None:
        return _IMPORT_CACHE

    if not _XIANYU_APIS_ROOT.exists():
        raise FileNotFoundError(f"未找到 XianYuApis 子仓库: {_XIANYU_APIS_ROOT}")

    sys.path.insert(0, str(_XIANYU_APIS_ROOT))
    old_cwd = os.getcwd()
    os.chdir(_XIANYU_APIS_ROOT)
    try:
        goofish_apis = importlib.import_module("goofish_apis")
        goofish_live = importlib.import_module("goofish_live")
        message = importlib.import_module("message")
        goofish_utils = importlib.import_module("utils.goofish_utils")
    finally:
        os.chdir(old_cwd)

    _IMPORT_CACHE = {
        "XianyuApis": goofish_apis.XianyuApis,
        "XianyuLive": goofish_live.XianyuLive,
        "make_text": message.make_text,
        "make_image": message.make_image,
        "trans_cookies": goofish_utils.trans_cookies,
        "generate_device_id": goofish_utils.generate_device_id,
    }
    return _IMPORT_CACHE


def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


class XianYuApiTools:
    def __init__(self, cookie_str: str):
        self.cookie_str = cookie_str.strip()
        self._api = None
        self._live = None

    def _require_cookie(self) -> None:
        if not self.cookie_str:
            raise ValueError(
                "未配置闲鱼 Cookie。请在 .env 中填写 XIANYU_COOKIE，或提供 XIANYU_COOKIE_FILE。"
            )

    def _get_api(self):
        self._require_cookie()
        if self._api is None:
            modules = _load_xianyu_modules()
            cookies = modules["trans_cookies"](self.cookie_str)
            if "unb" not in cookies:
                raise ValueError("Cookie 中缺少 unb 字段，无法生成 device_id。")
            device_id = modules["generate_device_id"](cookies["unb"])
            self._api = modules["XianyuApis"](cookies, device_id)
        return self._api

    def _get_live(self):
        self._require_cookie()
        if self._live is None:
            modules = _load_xianyu_modules()
            self._live = modules["XianyuLive"](self.cookie_str)
        return self._live

    def validate_login(self) -> str:
        result = self._get_api().get_token()
        token = result.get("data", {}).get("accessToken", "")
        return _dump(
            {
                "success": bool(token),
                "message": "登录态有效" if token else "未拿到 accessToken，请检查 Cookie 是否失效",
                "access_token_preview": token[:16] + "..." if token else "",
                "raw": result,
            }
        )

    def refresh_login(self) -> str:
        result = self._get_api().refresh_token()
        return _dump(
            {
                "success": "data" in result or "ret" in result,
                "raw": result,
            }
        )

    def get_item_detail(self, item_id: str) -> str:
        result = self._get_api().get_item_info(item_id)
        return _dump(result)

    async def list_conversation_messages(self, cid: str, max_items: int = 50) -> str:
        messages = await self._get_live().list_all_conversations(cid)
        if max_items > 0:
            messages = messages[-max_items:]
        return _dump(
            {
                "success": True,
                "count": len(messages),
                "messages": messages,
            }
        )

    async def send_text_message(self, to_user_id: str, item_id: str, text: str) -> str:
        modules = _load_xianyu_modules()
        await self._get_live().send_msg_once(
            to_user_id,
            item_id,
            modules["make_text"](text),
        )
        return _dump(
            {
                "success": True,
                "message": "文本消息已发送",
                "to_user_id": to_user_id,
                "item_id": item_id,
            }
        )

    async def send_image_message(self, to_user_id: str, item_id: str, image: str) -> str:
        modules = _load_xianyu_modules()
        image_path, should_cleanup = self._prepare_image(image)
        try:
            upload_result = await asyncio.to_thread(self._get_api().upload_media, image_path)
            image_object = upload_result.get("object", {})
            image_url = image_object.get("url")
            if not image_url:
                raise RuntimeError(f"图片上传失败: {_dump(upload_result)}")
            width, height = self._parse_pix(image_object.get("pix", "0x0"))
            await self._get_live().send_msg_once(
                to_user_id,
                item_id,
                modules["make_image"](image_url, width, height),
            )
            return _dump(
                {
                    "success": True,
                    "message": "图片消息已发送",
                    "to_user_id": to_user_id,
                    "item_id": item_id,
                    "upload": upload_result,
                }
            )
        finally:
            if should_cleanup:
                Path(image_path).unlink(missing_ok=True)

    def _prepare_image(self, image: str) -> tuple[str, bool]:
        if image.startswith("http://") or image.startswith("https://"):
            response = requests.get(image, timeout=30)
            response.raise_for_status()
            suffix = Path(image).suffix or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(response.content)
                return temp_file.name, True

        image_path = Path(image).expanduser()
        if not image_path.is_absolute():
            image_path = (Path.cwd() / image_path).resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        return str(image_path), False

    @staticmethod
    def _parse_pix(pix: str) -> tuple[int, int]:
        try:
            width_str, height_str = pix.lower().split("x", 1)
            return int(width_str), int(height_str)
        except Exception:
            return 0, 0
