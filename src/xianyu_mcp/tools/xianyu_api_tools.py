from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import requests
import websockets

from ..guardrails import RequestGuardrails

_REPO_ROOT = Path(__file__).resolve().parents[3]
_XIANYU_APIS_ROOT = _REPO_ROOT / "third_party" / "pyxianyu"  # src/xianyu_mcp/tools -> src/xianyu_mcp -> src -> 仓库根

_IMPORT_CACHE: dict[str, Any] | None = None


def _load_xianyu_modules() -> dict[str, Any]:
    global _IMPORT_CACHE
    if _IMPORT_CACHE is not None:
        return _IMPORT_CACHE

    if not _XIANYU_APIS_ROOT.exists():
        raise FileNotFoundError(f"未找到 pyxianyu 子仓库: {_XIANYU_APIS_ROOT}")

    sys.path.insert(0, str(_XIANYU_APIS_ROOT))
    old_cwd = os.getcwd()
    os.chdir(_XIANYU_APIS_ROOT)
    try:
        apis = importlib.import_module("apis")
        core = importlib.import_module("core")
        goofish_live = importlib.import_module("goofish_live")
        message = importlib.import_module("message")
        goofish_utils = importlib.import_module("utils.goofish_utils")
    finally:
        os.chdir(old_cwd)

    _IMPORT_CACHE = {
        "XianyuClient": core.XianyuClient,
        "AuthApi": apis.AuthApi,
        "ItemApi": apis.ItemApi,
        "MediaApi": apis.MediaApi,
        "SearchApi": getattr(apis, "SearchApi", None),
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
        self._client = None
        self._auth_api = None
        self._item_api = None
        self._media_api = None
        self._search_api = None
        self._live = None
        self._guardrails = RequestGuardrails()

    def _require_cookie(self) -> None:
        if not self.cookie_str:
            raise ValueError(
                "未配置闲鱼 Cookie。请在 .env 中填写 XIANYU_COOKIE，或提供 XIANYU_COOKIE_FILE。"
            )

    def _ensure_m_h5_tk(self, cookies: dict[str, str]) -> dict[str, str]:
        if cookies.get("_m_h5_tk"):
            return cookies

        t = str(int(time.time() * 1000))
        url = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/"
        params = {
            "jsv": "2.7.2",
            "appKey": "34839810",
            "t": t,
            "sign": "",
            "v": "1.0",
            "type": "originaljson",
            "dataType": "json",
            "timeout": "20000",
            "api": "mtop.taobao.idlemessage.pc.login.token",
            "sessionOption": "AutoLoginOnly",
        }
        headers = {
            "accept": "application/json",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7,ja;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.goofish.com",
            "pragma": "no-cache",
            "referer": "https://www.goofish.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
        }
        try:
            bootstrap_cookies: dict[str, str] = {}
            if cookies.get("cookie2"):
                bootstrap_cookies["cookie2"] = cookies["cookie2"]
            resp = requests.post(
                url,
                params=params,
                headers=headers,
                data={"data": "{}"},
                cookies=bootstrap_cookies,
                timeout=30,
            )
            resp.raise_for_status()
            for k, v in resp.cookies.items():
                cookies[k] = v
        except requests.RequestException:
            return cookies

        return cookies

    def _ensure_rest_apis(self) -> None:
        self._require_cookie()
        if self._client is None:
            modules = _load_xianyu_modules()
            cookies = modules["trans_cookies"](self.cookie_str)
            cookies = self._ensure_m_h5_tk(cookies)
            if "unb" not in cookies:
                raise ValueError("Cookie 中缺少 unb 字段，无法生成 device_id。")
            device_id = modules["generate_device_id"](cookies["unb"])
            self._client = modules["XianyuClient"](cookies, device_id)
            self._auth_api = modules["AuthApi"](self._client)
            self._item_api = modules["ItemApi"](self._client)
            self._media_api = modules["MediaApi"](self._client)
            if modules.get("SearchApi"):
                self._search_api = modules["SearchApi"](self._client)

    def _get_auth_api(self):
        self._ensure_rest_apis()
        return self._auth_api

    def _get_item_api(self):
        self._ensure_rest_apis()
        return self._item_api

    def _get_media_api(self):
        self._ensure_rest_apis()
        return self._media_api

    def _get_search_api(self):
        self._ensure_rest_apis()
        if self._search_api is None:
            raise RuntimeError("SearchApi 未加载，请确认 third_party/pyxianyu 已更新。")
        return self._search_api

    def _get_live(self):
        self._require_cookie()
        if self._live is None:
            modules = _load_xianyu_modules()
            self._live = modules["XianyuLive"](self.cookie_str)
        return self._live

    def validate_login(self) -> str:
        result = self._guardrails.run_read(lambda: self._get_auth_api().get_token())
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
        result = self._guardrails.run_read(lambda: self._get_auth_api().refresh_token())
        return _dump(
            {
                "success": "data" in result or "ret" in result,
                "raw": result,
            }
        )

    def get_item_detail(self, item_id: str) -> str:
        result = self._guardrails.run_read(lambda: self._get_item_api().get_item_info(item_id))
        return _dump(result)

    @staticmethod
    def _normalize_search_price(price: Any) -> str:
        if isinstance(price, str):
            return price
        if isinstance(price, (int, float)):
            return str(price)
        if isinstance(price, list):
            texts: list[str] = []
            for part in price:
                if isinstance(part, dict) and "text" in part:
                    texts.append(str(part.get("text") or ""))
            return "".join(texts).strip()
        return ""

    @staticmethod
    def _get_nested(data: Any, *keys: str) -> Any:
        cur = data
        for key in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
        return cur

    def search_items(
        self,
        keyword: str,
        *,
        page_number: int = 1,
        rows_per_page: int = 20,
        sort_field: str = "",
        sort_value: str = "",
        prop_value_str: dict[str, Any] | None = None,
        extra_filter_value: str = "{}",
        from_filter: bool = False,
    ) -> str:
        normalized_keyword = str(keyword).strip()
        if not normalized_keyword:
            raise ValueError("keyword 不能为空。")

        normalized_page_number = max(int(page_number), 1)
        normalized_rows_per_page = min(max(int(rows_per_page), 1), 50)
        normalized_sort_field = str(sort_field or "").strip()
        normalized_sort_value = str(sort_value or "").strip()

        result = self._guardrails.run_read(
            lambda: self._get_search_api().search_items(
                normalized_keyword,
                page_number=normalized_page_number,
                rows_per_page=normalized_rows_per_page,
                sort_field=normalized_sort_field,
                sort_value=normalized_sort_value,
                prop_value_str=prop_value_str,
                extra_filter_value=extra_filter_value,
                from_filter=from_filter,
            )
        )

        data = result.get("data", {}) or {}
        result_list = data.get("resultList") or []
        items: list[dict[str, Any]] = []
        for entry in result_list:
            ex_content = self._get_nested(entry, "data", "item", "main", "exContent") or {}
            if not isinstance(ex_content, dict):
                continue
            items.append(
                {
                    "item_id": ex_content.get("itemId") or "",
                    "title": ex_content.get("title") or "",
                    "price": self._normalize_search_price(ex_content.get("price")),
                    "pic_url": ex_content.get("picUrl") or "",
                    "area": ex_content.get("area") or "",
                    "user_nick_name": ex_content.get("userNickName") or "",
                }
            )

        result_info = data.get("resultInfo", {}) or {}
        return _dump(
            {
                "success": True,
                "api": result.get("api"),
                "keyword": normalized_keyword,
                "page_number": normalized_page_number,
                "rows_per_page": normalized_rows_per_page,
                "count": len(items),
                "has_next_page": bool(result_info.get("hasNextPage")),
                "items": items,
                "raw": result,
            }
        )

    def get_item_edit_detail(self, item_id: str) -> str:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id:
            raise ValueError("item_id 不能为空。")
        result = self._guardrails.run_read(
            lambda: self._get_item_api().get_item_edit_detail(normalized_item_id)
        )
        return _dump(result)

    def list_my_items(self, page_size: int = 20) -> str:
        normalized_page_size = min(max(page_size, 1), 50)
        user_id = self._get_current_user_id()
        result = self._guardrails.run_read(
            lambda: self._get_item_api().get_all_user_items(
                user_id=user_id,
                page_size=normalized_page_size,
            )
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

        result = self._guardrails.run_write(
            lambda: self._get_item_api().downshelf_item(normalized_item_id)
        )
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
        result = self._guardrails.run_write(
            lambda: self._get_item_api().reshelf_item(
                normalized_item_id,
                source_id=normalized_source_id or None,
            )
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

    def edit_item(
        self,
        item_id: str,
        *,
        overrides: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> str:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id:
            raise ValueError("item_id 不能为空。")

        if payload is not None and overrides is not None:
            raise ValueError("payload 与 overrides 互斥，请仅提供其中一个。")
        if payload is None and overrides is None:
            raise ValueError("payload 与 overrides 至少需要提供一个。")

        api = self._get_item_api()

        def run(call):
            edit_detail = None
            if payload is not None:
                request_payload = dict(payload or {})
                request_payload["itemId"] = normalized_item_id
                mode = "payload"
            else:
                edit_detail = call(lambda: api.get_item_edit_detail(normalized_item_id))
                request_payload = api.build_reshelf_payload(edit_detail, item_id=normalized_item_id)
                normalized_overrides = dict(overrides or {})
                mode = "overrides"
                if "title" in normalized_overrides:
                    item_text = dict(request_payload.get("itemTextDTO") or {})
                    item_text["title"] = str(normalized_overrides.pop("title")).strip()
                    request_payload["itemTextDTO"] = item_text
                if "desc" in normalized_overrides:
                    item_text = dict(request_payload.get("itemTextDTO") or {})
                    item_text["desc"] = str(normalized_overrides.pop("desc"))
                    request_payload["itemTextDTO"] = item_text
                if "price" in normalized_overrides:
                    price_in_cent = str(
                        int(float(str(normalized_overrides.pop("price")).strip()) * 100)
                    )
                    item_price = dict(request_payload.get("itemPriceDTO") or {})
                    item_price["priceInCent"] = price_in_cent
                    request_payload["itemPriceDTO"] = item_price
                if normalized_overrides:
                    self._deep_update(request_payload, normalized_overrides)

            edit_result = call(lambda: api.edit_item(request_payload))
            return edit_detail, request_payload, edit_result, mode

        edit_detail, request_payload, edit_result, mode = self._guardrails.run_write_steps(run)
        edit_data = edit_result.get("data", {}) or {}
        ret = edit_result.get("ret") or []
        success = bool(edit_data.get("success")) or any(
            isinstance(item, str) and item.startswith("SUCCESS") for item in ret
        )
        return _dump(
            {
                "success": success,
                "item_id": normalized_item_id,
                "api": edit_result.get("api"),
                "raw": {
                    "itemId": normalized_item_id,
                    "mode": mode,
                    "editDetail": edit_detail,
                    "editPayload": request_payload,
                    "editResult": edit_result,
                },
            }
        )

    def publish_physical_item(
        self,
        title: str,
        price: str,
        desc: str,
        images: list[str],
    ) -> str:
        if not images:
            raise ValueError("至少需要一张商品图片。")
        if not title.strip():
            raise ValueError("商品标题不能为空。")
        if not price.strip():
            raise ValueError("商品价格不能为空。")

        api = self._get_item_api()
        media_api = self._get_media_api()
        publish_template = self._guardrails.run_read(lambda: api.preget())

        def run(call):
            request_payload = api.build_reshelf_payload(publish_template)
            request_payload.pop("itemId", None)
            request_payload["sourceId"] = "publish"

            uploaded_images = []
            temp_paths: list[str] = []
            try:
                for image_path in images:
                    local_path, should_cleanup = self._prepare_media(image_path)
                    if should_cleanup:
                        temp_paths.append(local_path)
                    upload_result = call(lambda: media_api.upload_media(local_path))
                    image_object = upload_result.get("object", {})
                    image_url = image_object.get("url", "")
                    if not image_url:
                        raise RuntimeError(f"图片上传失败: {image_path}")
                    uploaded_images.append(
                        {
                            "url": image_url,
                            "major": "true" if len(uploaded_images) == 0 else "false",
                        }
                    )

                item_text = dict(request_payload.get("itemTextDTO") or {})
                item_text["title"] = title.strip()
                item_text["desc"] = desc.strip()
                request_payload["itemTextDTO"] = item_text

                item_price = dict(request_payload.get("itemPriceDTO") or {})
                item_price["priceInCent"] = str(int(float(price) * 100))
                if "currency" not in item_price:
                    item_price["currency"] = "CNY"
                request_payload["itemPriceDTO"] = item_price

                request_payload["imageInfoDOList"] = uploaded_images
                return call(lambda: api.publish_item(request_payload))
            finally:
                for path in temp_paths:
                    Path(path).unlink(missing_ok=True)

        result = self._guardrails.run_write_steps(run)
        new_item_id = (result.get("data", {}) or {}).get("itemId", "")
        success = bool(new_item_id) or any(
            isinstance(item, str) and item.startswith("SUCCESS")
            for item in (result.get("ret") or [])
        )
        return _dump(
            {
                "success": success,
                "item_id": new_item_id,
                "api": result.get("api"),
                "raw": result,
            }
        )

    def upload_media(self, media: str) -> str:
        media_path, should_cleanup = self._prepare_media(media)
        try:
            def run(call):
                return call(lambda: self._get_media_api().upload_media(media_path))

            upload_result = self._guardrails.run_write_steps(run)
            image_object = upload_result.get("object", {}) or {}
            url = str(image_object.get("url") or "").strip()
            pix = str(image_object.get("pix") or "").strip()
            width, height = self._parse_pix(pix) if pix else (0, 0)
            return _dump(
                {
                    "success": bool(url),
                    "url": url,
                    "pix": pix,
                    "width": width,
                    "height": height,
                    "raw": upload_result,
                }
            )
        finally:
            if should_cleanup:
                Path(media_path).unlink(missing_ok=True)

    @staticmethod
    def _deep_update(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        for key, value in patch.items():
            if (
                key in target
                and isinstance(target.get(key), dict)
                and isinstance(value, dict)
            ):
                XianYuApiTools._deep_update(target[key], value)
            else:
                target[key] = value
        return target

    async def list_conversations(
        self,
        max_items: int = 1000,
        include_hidden: bool = False,
    ) -> str:
        normalized_max_items = min(max(max_items, 1), 1000)
        conversations = await self._guardrails.run_read_async(
            lambda: self._fetch_conversations(normalized_max_items)
        )
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
        messages = await self._guardrails.run_read_async(
            lambda: self._get_live().list_all_conversations(cid)
        )
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

        async def send():
            await self._get_live().send_msg_once(
                to_user_id,
                item_id,
                modules["make_text"](text),
            )

        await self._guardrails.run_write_async(send)
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
        image_path, should_cleanup = self._prepare_media(image)
        try:
            async def run(call):
                upload_result = await call(
                    lambda: asyncio.to_thread(self._get_media_api().upload_media, image_path)
                )
                image_object = upload_result.get("object", {})
                image_url = image_object.get("url")
                if not image_url:
                    raise RuntimeError(f"图片上传失败: {_dump(upload_result)}")
                width, height = self._parse_pix(image_object.get("pix", "0x0"))
                await call(
                    lambda: self._get_live().send_msg_once(
                        to_user_id,
                        item_id,
                        modules["make_image"](image_url, width, height),
                    )
                )
                return upload_result

            upload_result = await self._guardrails.run_write_steps_async(run)
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

    def _prepare_media(self, media: str) -> tuple[str, bool]:
        return self._prepare_image(media)

    def _prepare_image(self, image: str) -> tuple[str, bool]:
        if image.startswith("http://") or image.startswith("https://"):
            headers = {
                "user-agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "referer": "https://www.goofish.com/",
                "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            }
            response = requests.get(image, headers=headers, timeout=30)
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
        api = self._get_auth_api()
        try:
            self._guardrails.run_read(lambda: api.get_token())
        except Exception:
            pass
        refresh_result = self._guardrails.run_read(lambda: api.refresh_token())
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
