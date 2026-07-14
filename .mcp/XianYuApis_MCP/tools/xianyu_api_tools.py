from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import requests
import websockets

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
        "generate_mid": goofish_utils.generate_mid,
        "trans_cookies": goofish_utils.trans_cookies,
        "generate_device_id": goofish_utils.generate_device_id,
    }
    return _IMPORT_CACHE


def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _session_cookies_str(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def _ws_connect(url: str, headers: dict[str, str]):
    kwargs: dict[str, Any] = {}
    parameters = inspect.signature(websockets.connect).parameters
    if "additional_headers" in parameters:
        kwargs["additional_headers"] = headers
    else:
        kwargs["extra_headers"] = headers
    if "proxy" in parameters:
        kwargs["proxy"] = None
    return websockets.connect(url, **kwargs)


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

    def get_item_edit_detail(self, item_id: str) -> str:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id:
            raise ValueError("item_id 不能为空。")
        result = self._get_api().get_item_edit_detail(normalized_item_id)
        return _dump(result)

    def list_my_items(self, page_size: int = 20) -> str:
        normalized_page_size = min(max(page_size, 1), 50)
        user_id = self._get_current_user_id()
        result = self._get_api().get_all_user_items(
            user_id=user_id,
            page_size=normalized_page_size,
        )
        groups = [
            {
                "group_id": group.get("groupId"),
                "group_name": group.get("groupName"),
                "item_number": group.get("itemNumber"),
                "group_type": group.get("groupType"),
                "default_group": group.get("defaultGroup"),
            }
            for group in (result.get("itemGroupList") or [])
        ]
        items = [self._normalize_item_card(card) for card in (result.get("cardList") or [])]
        return _dump(
            {
                "success": True,
                "api": result.get("api"),
                "user_id": user_id,
                "count": len(items),
                "page_size": normalized_page_size,
                "page_count": result.get("pageCount", 0),
                "pages": result.get("pages", []),
                "groups": groups,
                "items": items,
                "raw": result,
            }
        )

    def downshelf_item(self, item_id: str) -> str:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id:
            raise ValueError("item_id 不能为空。")

        result = self._get_api().downshelf_item(normalized_item_id)
        return _dump(
            {
                "success": bool(result.get("data", {}).get("success")),
                "item_id": normalized_item_id,
                "api": result.get("api"),
                "raw": result,
            }
        )

    def reshelf_item(self, item_id: str, source_id: str = "") -> str:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id:
            raise ValueError("item_id 不能为空。")

        normalized_source_id = str(source_id).strip()
        result = self._get_api().reshelf_item(
            normalized_item_id,
            source_id=normalized_source_id or None,
        )
        edit_result = result.get("editResult", {}) or {}
        edit_data = edit_result.get("data", {}) or {}
        edit_payload = result.get("editPayload", {}) or {}
        ret = edit_result.get("ret") or []
        success = bool(edit_data.get("success")) or any(
            isinstance(item, str) and item.startswith("SUCCESS") for item in ret
        )
        return _dump(
            {
                "success": success,
                "item_id": normalized_item_id,
                "source_id": edit_payload.get("sourceId", ""),
                "api": edit_result.get("api"),
                "raw": result,
            }
        )

    async def list_conversations(
        self,
        max_items: int = 1000,
        include_hidden: bool = False,
    ) -> str:
        normalized_max_items = min(max(max_items, 1), 1000)
        conversations = await self._fetch_conversations(normalized_max_items)
        summaries = [self._normalize_conversation(conversation) for conversation in conversations]
        if not include_hidden:
            summaries = [summary for summary in summaries if summary.get("visible", True)]
        return _dump(
            {
                "success": True,
                "count": len(summaries),
                "raw_count": len(conversations),
                "max_items": normalized_max_items,
                "include_hidden": include_hidden,
                "conversations": summaries,
            }
        )

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

    def _get_current_user_id(self) -> str:
        api = self._get_api()
        # 先换一次 accessToken，避免直接读 loginuser.get 时命中旧 token 过期。
        api.get_token()
        refresh_result = api.refresh_token()
        user_id = str(refresh_result.get("data", {}).get("userId", "")).strip()
        if not user_id:
            raise RuntimeError(f"未从登录态响应中拿到 userId: {_dump(refresh_result)}")
        return user_id

    def _normalize_item_card(self, card: dict[str, Any]) -> dict[str, Any]:
        card_data = card.get("cardData", {}) if isinstance(card, dict) else {}
        detail_params = card_data.get("detailParams", {}) or {}
        pic_info = card_data.get("picInfo", {}) or {}
        price_info = card_data.get("priceInfo", {}) or {}
        item_status = card_data.get("itemStatus")
        return {
            "item_id": card_data.get("id") or detail_params.get("itemId"),
            "title": card_data.get("title") or detail_params.get("title"),
            "price": price_info.get("price") or detail_params.get("soldPrice"),
            "price_prefix": price_info.get("preText"),
            "status": self._item_status_text(item_status),
            "status_code": item_status,
            "category_id": detail_params.get("categoryId"),
            "want_text": detail_params.get("wantText"),
            "main_pic_url": pic_info.get("picUrl") or detail_params.get("picUrl"),
            "detail_url": card_data.get("detailUrl"),
            "raw": card,
        }

    @staticmethod
    def _item_status_text(item_status: Any) -> str:
        mapping = {
            0: "在线",
            1: "已售出",
            -2: "已下架",
        }
        return mapping.get(item_status, str(item_status) if item_status is not None else "")

    async def _fetch_conversations(self, max_items: int) -> list[dict[str, Any]]:
        live = self._get_live()
        modules = _load_xianyu_modules()
        headers = {
            "Cookie": _session_cookies_str(live.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            ),
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        async with _ws_connect(live.base_url, headers) as websocket:
            await live.init(websocket)
            send_mid = modules["generate_mid"]()
            request_message = {
                "lwp": "/r/Conversation/listNewest",
                "headers": {"mid": send_mid},
                "body": [0, max_items],
            }
            request_sent = False
            async for raw_message in websocket:
                message = self._safe_json_load(raw_message)
                if not isinstance(message, dict):
                    continue
                await self._ack_ws_message(websocket, message)
                if not request_sent and message.get("lwp") == "/s/vulcan":
                    await websocket.send(json.dumps(request_message))
                    request_sent = True
                    continue
                if message.get("headers", {}).get("mid") == send_mid:
                    body = message.get("body")
                    return body if isinstance(body, list) else []
        return []

    async def _ack_ws_message(self, websocket: Any, message: dict[str, Any]) -> None:
        headers = message.get("headers", {})
        if not isinstance(headers, dict) or not headers:
            return
        ack_headers = {
            "mid": headers.get("mid", ""),
            "sid": headers.get("sid", ""),
        }
        for key in ("app-key", "ua", "dt"):
            if key in headers:
                ack_headers[key] = headers[key]
        await websocket.send(json.dumps({"code": 200, "headers": ack_headers}))

    def _normalize_conversation(self, conversation: dict[str, Any]) -> dict[str, Any]:
        if "singleChatUserConversation" in conversation:
            return self._normalize_single_conversation(conversation["singleChatUserConversation"])
        if "groupChatUserConversation" in conversation:
            return self._normalize_group_conversation(conversation["groupChatUserConversation"])
        return {
            "conversation_type": "unknown",
            "visible": True,
            "raw_type": conversation.get("type"),
        }

    def _normalize_single_conversation(self, user_conversation: dict[str, Any]) -> dict[str, Any]:
        conversation = user_conversation.get("singleChatConversation", {})
        extension = conversation.get("extension", {})
        last_message = (user_conversation.get("lastMessage", {}) or {}).get("message", {}) or {}
        last_extension = last_message.get("extension", {}) or {}
        peer_user_id = self._resolve_peer_user_id(conversation, extension)
        last_sender_id = last_extension.get("senderUserId", "")
        last_sender_name_hint = last_extension.get("reminderTitle", "")
        peer_user_name_hint = last_sender_name_hint if last_sender_id == peer_user_id else ""
        return {
            "conversation_type": "single",
            "cid": self._strip_goofish_suffix(conversation.get("cid", "")),
            "visible": user_conversation.get("visible", 1) == 1,
            "unread_count": user_conversation.get("redPoint", 0),
            "is_top": bool(user_conversation.get("topRank", 0)),
            "modify_time": user_conversation.get("modifyTime", 0),
            "item_id": extension.get("itemId", ""),
            "item_title": extension.get("itemTitle", ""),
            "peer_user_id": peer_user_id,
            "peer_user_type": extension.get("extUserType", ""),
            "peer_user_name_hint": peer_user_name_hint,
            "last_message_summary": self._get_message_summary(last_message),
            "last_sender_user_id": last_sender_id,
            "last_sender_name_hint": last_sender_name_hint,
            "biz_type": conversation.get("bizType", ""),
            "red_reminder": (user_conversation.get("user_extension", {}) or {}).get("redReminder", ""),
        }

    def _normalize_group_conversation(self, user_conversation: dict[str, Any]) -> dict[str, Any]:
        conversation = user_conversation.get("groupChatConversation", {})
        extension = conversation.get("extension", {})
        last_message = (user_conversation.get("lastMessage", {}) or {}).get("message", {}) or {}
        last_extension = last_message.get("extension", {}) or {}
        return {
            "conversation_type": "group",
            "cid": self._strip_goofish_suffix(conversation.get("cid", "")),
            "visible": user_conversation.get("visible", 1) == 1,
            "unread_count": user_conversation.get("redPoint", 0),
            "is_top": bool(user_conversation.get("topRank", 0)),
            "modify_time": user_conversation.get("modifyTime", 0),
            "title": self._parse_group_title(conversation, extension),
            "member_count": conversation.get("memberCount", 0),
            "biz_type": conversation.get("bizType", ""),
            "last_message_summary": self._get_message_summary(last_message),
            "last_sender_user_id": last_extension.get("senderUserId", ""),
            "last_sender_name_hint": last_extension.get("reminderTitle", ""),
        }

    def _resolve_peer_user_id(
        self,
        conversation: dict[str, Any],
        extension: dict[str, Any],
    ) -> str:
        peer_user_id = str(extension.get("extUserId", "")).strip()
        if peer_user_id:
            return peer_user_id
        my_user_id = getattr(self._get_live(), "myid", "")
        for key in ("pairFirst", "pairSecond"):
            user_id = self._strip_goofish_suffix(conversation.get(key, ""))
            if user_id and user_id != my_user_id:
                return user_id
        return ""

    @staticmethod
    def _safe_json_load(raw_message: Any) -> Any:
        if isinstance(raw_message, (dict, list)):
            return raw_message
        try:
            return json.loads(raw_message)
        except Exception:
            return None

    @staticmethod
    def _strip_goofish_suffix(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.removesuffix("@goofish")

    @staticmethod
    def _get_message_summary(message: dict[str, Any]) -> str:
        content = (message.get("content", {}) or {}).get("custom", {}) or {}
        extension = message.get("extension", {}) or {}
        return content.get("summary", "") or extension.get("reminderContent", "")

    @staticmethod
    def _parse_group_title(conversation: dict[str, Any], extension: dict[str, Any]) -> str:
        for value in (extension.get("title", ""), conversation.get("title", "")):
            parsed = XianYuApiTools._parse_title_value(value)
            if parsed:
                return parsed
        return ""

    @staticmethod
    def _parse_title_value(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("def", "")).strip()
        if not isinstance(value, str):
            return ""
        value = value.strip()
        if not value:
            return ""
        try:
            parsed = json.loads(value)
        except Exception:
            return value
        if isinstance(parsed, dict):
            return str(parsed.get("def", "")).strip() or value
        return value

    @staticmethod
    def _parse_pix(pix: str) -> tuple[int, int]:
        try:
            width_str, height_str = pix.lower().split("x", 1)
            return int(width_str), int(height_str)
        except Exception:
            return 0, 0
