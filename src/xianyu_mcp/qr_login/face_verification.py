from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger

from .parsing import (
    extract_face_qr_content,
    extract_htoken,
    extract_verify_modes_url,
)
from .utils import render_qr_data_url

if TYPE_CHECKING:
    from .manager import QRLoginManager


async def run_face_verification(manager: "QRLoginManager", session_id: str, iframe_url: str) -> None:
    session = manager.sessions.get(session_id)
    if not session:
        return

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=manager.timeout,
            proxy=manager.proxy,
            cookies=session.cookies,
            headers=manager.headers,
        ) as client:
            resp = await client.get(iframe_url)
            normal_html = resp.text

            htoken = extract_htoken(normal_html)
            verify_modes_url = extract_verify_modes_url(normal_html)

            resp = await client.get(verify_modes_url)
            identity_html = resp.text

            face_qr_content = extract_face_qr_content(identity_html)
            session.face_qr_content = face_qr_content
            session.face_qr_data_url = render_qr_data_url(face_qr_content)

            check_headers = dict(manager.headers)
            check_headers.update(
                {
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{manager.host}/iv/mini/identity_verify.htm?htoken={htoken}",
                }
            )

            iv_check_url: str | None = None
            while not session.is_expired():
                if session_id not in manager.sessions:
                    return
                check_resp = await client.get(
                    manager.api_face_check,
                    params={"htoken": htoken},
                    headers=check_headers,
                )
                try:
                    payload: dict[str, Any] = check_resp.json()
                except Exception:
                    payload = {}
                content = payload.get("content") or {}
                code = str(content.get("code", ""))
                if code == "3":
                    iv_check_url = content.get("url")
                    break
                await asyncio.sleep(2)

            if not iv_check_url:
                session.status = "expired"
                return

            await client.get(iv_check_url, headers=check_headers)
            for cookie_name, cookie_value in client.cookies.items():
                session.cookies[cookie_name] = cookie_value
                if cookie_name == "unb":
                    session.unb = cookie_value

            if session.unb:
                await manager._bootstrap_mtop_cookies(session_id)
                if manager._has_mtop_token(session):
                    session.status = "success"
                    return
                if session.status != "verification_required":
                    session.status = "verification_required"
                    session.created_time = time.time()
                    session.expire_time = 900.0
                await manager._monitor_mtop_bootstrap(session_id)
            else:
                session.status = "expired"
    except Exception as e:
        logger.warning(f"人脸验证失败: {session_id}: {type(e).__name__}")
        if session_id in manager.sessions:
            manager.sessions[session_id].status = "error"
            manager.sessions[session_id].error_message = "人脸验证失败"
