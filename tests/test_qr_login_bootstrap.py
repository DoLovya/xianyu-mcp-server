from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from xianyu_mcp.qr_login.manager import QRLoginManager
from xianyu_mcp.qr_login.models import QRLoginSession


class _FakeResponse:
    def __init__(self, cookies: dict[str, str], payload: object | None = None) -> None:
        self._cookies = cookies
        self._payload = payload if payload is not None else {}

    @property
    def cookies(self):
        return self

    def items(self):
        return self._cookies.items()

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, *args, **kwargs):
        return self._response


class TestQRLoginBootstrap(unittest.TestCase):
    def test_find_verification_url(self) -> None:
        payload = {
            "content": {
                "data": {
                    "url": "https://passport.goofish.com/punish?x=1",
                }
            }
        }
        self.assertEqual(QRLoginManager._find_verification_url(payload), payload["content"]["data"]["url"])

    def test_bootstrap_marks_verification_required_without_cookie2(self) -> None:
        manager = QRLoginManager()
        session_id = "s1"
        session = QRLoginSession(session_id=session_id)
        manager.sessions[session_id] = session

        asyncio.run(manager._bootstrap_mtop_cookies(session_id))

        self.assertEqual(session.status, "verification_required")
        self.assertGreaterEqual(session.expire_time, 900.0)

    def test_bootstrap_merges_mtop_token(self) -> None:
        manager = QRLoginManager()
        session_id = "s2"
        session = QRLoginSession(session_id=session_id)
        session.cookies["cookie2"] = "c2"
        manager.sessions[session_id] = session

        fake_resp = _FakeResponse(
            cookies={"_m_h5_tk": "tk_x", "_m_h5_tk_enc": "enc_x"},
            payload={"ret": ["SUCCESS::调用成功"]},
        )

        def factory(*args, **kwargs):
            return _FakeAsyncClient(fake_resp)

        async def run():
            with patch("xianyu_mcp.qr_login.manager.httpx.AsyncClient", side_effect=factory):
                await manager._bootstrap_mtop_cookies(session_id)

        asyncio.run(run())

        self.assertIn("_m_h5_tk", session.cookies)
        self.assertIn("_m_h5_tk_enc", session.cookies)
        self.assertTrue(manager._has_mtop_token(session))


if __name__ == "__main__":
    unittest.main()

