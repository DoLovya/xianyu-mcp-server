from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from random import random
from typing import Any

import httpx
from loguru import logger

from .face_verification import run_face_verification
from .models import QRLoginSession
from .parsing import extract_login_form_data
from .utils import cookies_dict_to_str, render_qr_data_url


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Referer": "https://passport.goofish.com/",
        "Origin": "https://passport.goofish.com",
    }


class QRLoginManager:
    def __init__(self) -> None:
        self.sessions: dict[str, QRLoginSession] = {}
        self._face_tasks: set[asyncio.Task[Any]] = set()
        self._mtop_tasks: set[asyncio.Task[Any]] = set()
        self.headers = _default_headers()
        self.host = "https://passport.goofish.com"
        self.api_mini_login = f"{self.host}/mini_login.htm"
        self.api_generate_qr = f"{self.host}/newlogin/qrcode/generate.do"
        self.api_scan_status = f"{self.host}/newlogin/qrcode/query.do"
        self.api_face_check = f"{self.host}/iv/photoVerify/check.do"
        self.api_mtop_login_token = (
            "https://h5api.m.goofish.com/h5/"
            "mtop.taobao.idlemessage.pc.login.token/1.0/"
        )
        self.api_h5_tk = (
            "https://h5api.m.goofish.com/h5/"
            "mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get/1.0/"
        )
        self.proxy = os.environ.get("XIANYU_QR_LOGIN_PROXY", "").strip() or None
        self.timeout = httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=60.0)

    @staticmethod
    def _has_mtop_token(session: QRLoginSession) -> bool:
        return bool(session.cookies.get("_m_h5_tk")) and bool(session.cookies.get("_m_h5_tk_enc"))

    @staticmethod
    def _has_x5sec(session: QRLoginSession) -> bool:
        return bool(session.cookies.get("x5sec"))

    @staticmethod
    def _find_verification_url(payload: Any) -> str | None:
        def walk(obj: Any, depth: int) -> str | None:
            if depth > 6:
                return None
            if isinstance(obj, str):
                if obj.startswith("http") and ("punish" in obj or "verify" in obj or "captcha" in obj):
                    return obj
                return None
            if isinstance(obj, dict):
                for value in obj.values():
                    hit = walk(value, depth + 1)
                    if hit:
                        return hit
                return None
            if isinstance(obj, list):
                for value in obj:
                    hit = walk(value, depth + 1)
                    if hit:
                        return hit
                return None
            return None

        return walk(payload, 0)

    async def _bootstrap_mtop_cookies(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return

        if self._has_mtop_token(session):
            return

        cookie2 = session.cookies.get("cookie2") or ""
        if not cookie2:
            session.status = "verification_required"
            session.error_message = "missing_cookie2"
            session.created_time = time.time()
            session.expire_time = 900.0
            return

        t = str(int(time.time() * 1000))
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

        payload: Any = {}
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.timeout,
                proxy=self.proxy,
            ) as client:
                resp = await client.post(
                    self.api_mtop_login_token,
                    params=params,
                    data={"data": "{}"},
                    headers=headers,
                    cookies={"cookie2": cookie2},
                )
                for k, v in resp.cookies.items():
                    session.cookies[k] = v
                    if k == "unb":
                        session.unb = v
                try:
                    payload = resp.json()
                except Exception:
                    payload = {}
        except Exception:
            payload = {}

        if self._has_mtop_token(session):
            session.error_message = None
            return

        verification_url = self._find_verification_url(payload)
        if verification_url:
            session.verification_url = verification_url

        session.status = "verification_required"
        session.error_message = "mtop_cookie_incomplete"
        session.created_time = time.time()
        session.expire_time = 900.0

    async def _monitor_mtop_bootstrap(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            while not session.is_expired():
                if session_id not in self.sessions:
                    return
                if session.status != "verification_required":
                    return
                await self._bootstrap_mtop_cookies(session_id)
                if self._has_mtop_token(session):
                    session.status = "success"
                    session.error_message = None
                    return
                await asyncio.sleep(2.0)
            if session.status == "verification_required":
                session.status = "expired"
        except Exception as e:
            logger.warning(f"mtop cookie 补齐失败: {session_id}: {type(e).__name__}")
            if session_id in self.sessions:
                self.sessions[session_id].status = "error"
                self.sessions[session_id].error_message = "mtop cookie 补齐失败"

    async def generate(self) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        session = QRLoginSession(session_id=session_id)
        self.sessions[session_id] = session

        try:
            try:
                await self._get_mh5tk(session)
            except ValueError as e:
                if str(e) != "missing_m_h5_tk":
                    raise
                logger.warning(
                    f"qr_login_generate 获取 m_h5_tk 失败，降级继续: {session_id}: {type(e).__name__}"
                )
            await self._get_login_params(session)
            await self._generate_qr(session)
            asyncio.create_task(self._monitor_qr_status(session_id))
            return {
                "success": True,
                **session.to_public_dict(),
            }
        except Exception as e:
            session.status = "error"
            session.error_message = "生成二维码失败"
            logger.warning(f"qr_login_generate 失败: {session_id}: {type(e).__name__}")
            return {
                "success": False,
                **session.to_public_dict(),
            }

    def get_status(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "status": "error",
                "message": "session_not_found",
                "session_id": session_id,
            }

        if session.is_expired() and session.status not in {"success", "verification_required"}:
            session.status = "expired"
        return {"success": True, **session.to_public_dict()}

    def get_cookie(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "status": "error",
                "message": "session_not_found",
                "session_id": session_id,
            }

        if session.status != "success":
            return {
                "success": False,
                **session.to_public_dict(),
                "message": "session_not_success",
            }

        return {
            "success": True,
            "session_id": session_id,
            "status": session.status,
            "unb": session.unb or "",
            "cookie": cookies_dict_to_str(session.cookies),
        }

    async def _get_mh5tk(self, session: QRLoginSession) -> None:
        data = {"bizScene": "home"}
        data_str = json.dumps(data, separators=(",", ":"))
        t = str(int(time.time() * 1000))
        app_key = "34839810"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            proxy=self.proxy,
        ) as client:
            resp = await client.get(self.api_h5_tk, headers=self.headers)
            for k, v in resp.cookies.items():
                session.cookies[k] = v

            mh5 = session.cookies.get("m_h5_tk") or session.cookies.get("_m_h5_tk") or ""
            token = mh5.split("_")[0] if "_" in mh5 else ""
            if not token:
                raise ValueError("missing_m_h5_tk")

            sign_input = f"{token}&{t}&{app_key}&{data_str}"
            sign = hashlib.md5(sign_input.encode()).hexdigest()
            params = {
                "jsv": "2.7.2",
                "appKey": app_key,
                "t": t,
                "sign": sign,
                "v": "1.0",
                "type": "originaljson",
                "dataType": "json",
                "timeout": 20000,
                "api": "mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get",
                "data": data_str,
            }
            await client.post(
                self.api_h5_tk,
                params=params,
                headers=self.headers,
                cookies=session.cookies,
            )

    async def _get_login_params(self, session: QRLoginSession) -> None:
        params = {
            "lang": "zh_cn",
            "appName": "xianyu",
            "appEntrance": "web",
            "styleType": "vertical",
            "bizParams": "",
            "notLoadSsoView": False,
            "notKeepLogin": False,
            "isMobile": False,
            "qrCodeFirst": False,
            "stie": 77,
            "rnd": random(),
        }
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout,
            proxy=self.proxy,
        ) as client:
            resp = await client.get(
                self.api_mini_login,
                params=params,
                cookies=session.cookies,
                headers=self.headers,
            )
            data = extract_login_form_data(resp.text)
            session.params.update(data)

    async def _generate_qr(self, session: QRLoginSession) -> None:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout,
            proxy=self.proxy,
        ) as client:
            resp = await client.get(self.api_generate_qr, params=session.params, headers=self.headers)
            results: dict[str, Any] = resp.json()
            content = results.get("content") or {}
            if content.get("success") is not True:
                raise ValueError("generate_qr_failed")
            data = content.get("data") or {}
            session.params.update({"t": data.get("t"), "ck": data.get("ck")})
            session.qr_content = str(data.get("codeContent") or "")
            if not session.qr_content:
                raise ValueError("missing_code_content")
            session.qr_data_url = render_qr_data_url(session.qr_content)
            session.status = "waiting"

    async def _poll_status(self, session: QRLoginSession) -> httpx.Response:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout,
            proxy=self.proxy,
        ) as client:
            return await client.post(
                self.api_scan_status,
                data=session.params,
                cookies=session.cookies,
                headers=self.headers,
            )

    async def _monitor_qr_status(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            while not session.is_expired():
                if session_id not in self.sessions:
                    return

                resp = await self._poll_status(session)
                payload: dict[str, Any] = {}
                try:
                    payload = resp.json()
                except Exception:
                    payload = {}
                data = (payload.get("content") or {}).get("data") or {}
                qr_status_raw = data.get("qrCodeStatus")
                qr_status = str(qr_status_raw).upper() if qr_status_raw else None

                if qr_status in {"CONFIRMED", "CONFIRM", "SUCCESS"}:
                    if data.get("iframeRedirect") is True:
                        session.status = "verification_required"
                        session.verification_url = data.get("iframeRedirectUrl")
                        for k, v in resp.cookies.items():
                            session.cookies[k] = v
                        session.created_time = time.time()
                        session.expire_time = 900.0
                        iframe_url = session.verification_url or ""
                        task = asyncio.create_task(run_face_verification(self, session_id, iframe_url))
                        self._face_tasks.add(task)
                        task.add_done_callback(self._face_tasks.discard)
                        return

                    for k, v in resp.cookies.items():
                        session.cookies[k] = v
                        if k == "unb":
                            session.unb = v
                    await self._bootstrap_mtop_cookies(session_id)
                    if self._has_mtop_token(session):
                        session.status = "success"
                        return
                    task = asyncio.create_task(self._monitor_mtop_bootstrap(session_id))
                    self._mtop_tasks.add(task)
                    task.add_done_callback(self._mtop_tasks.discard)
                    return

                if qr_status in {"SCANED", "SCANNED"} and session.status == "waiting":
                    session.status = "scanned"
                elif qr_status == "EXPIRED":
                    session.status = "expired"
                    return
                elif qr_status in {"NEW", None}:
                    pass
                elif qr_status in {"CANCELLED", "CANCELED", "CANCEL"}:
                    session.status = "cancelled"
                    return
                else:
                    session.error_message = f"unknown_qrCodeStatus:{qr_status}"

                await asyncio.sleep(0.8)

            if session.status not in {"success", "verification_required"}:
                session.status = "expired"
        except Exception as e:
            logger.warning(f"二维码轮询失败: {session_id}: {type(e).__name__}")
            if session_id in self.sessions:
                self.sessions[session_id].status = "error"
                self.sessions[session_id].error_message = "二维码轮询失败"
