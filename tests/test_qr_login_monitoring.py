from __future__ import annotations

import asyncio
import threading
import unittest
from unittest.mock import patch

from xianyu_mcp.qr_login.manager import QRLoginManager
from xianyu_mcp.qr_login.models import QRLoginSession

_REAL_THREAD = threading.Thread


class _FakeResponse:
    def __init__(self, cookies: dict[str, str], payload: dict) -> None:
        self._cookies = cookies
        self._payload = payload

    @property
    def cookies(self):
        return self

    def items(self):
        return self._cookies.items()

    def json(self):
        return self._payload


class _ImmediateThread:
    def __init__(self, *, target, name: str | None = None, daemon: bool | None = None) -> None:
        self._thread = _REAL_THREAD(target=target, name=name, daemon=daemon)

    def start(self) -> None:
        self._thread.start()
        self._thread.join(timeout=2.0)


class TestQRLoginMonitoring(unittest.TestCase):
    def test_generate_starts_monitor_thread_even_under_asyncio_run(self) -> None:
        manager = QRLoginManager()

        async def noop(*args, **kwargs):
            return None

        async def fake_generate_qr(self, session: QRLoginSession) -> None:
            session.status = "waiting"
            session.qr_data_url = "data:image/png;base64,abc"

        async def fake_monitor(self, session_id: str) -> None:
            session = manager.sessions.get(session_id)
            if session:
                session.status = "scanned"

        with (
            patch("xianyu_mcp.qr_login.manager.threading.Thread", _ImmediateThread),
            patch.object(QRLoginManager, "_get_mh5tk", new=noop),
            patch.object(QRLoginManager, "_get_login_params", new=noop),
            patch.object(QRLoginManager, "_generate_qr", new=fake_generate_qr),
            patch.object(QRLoginManager, "_monitor_qr_status", new=fake_monitor),
        ):
            result = asyncio.run(manager.generate())

        self.assertTrue(result["success"])
        session_id = result["session_id"]
        self.assertEqual(manager.sessions[session_id].status, "scanned")

    def test_monitor_confirmed_can_reach_success_without_spawning_tasks(self) -> None:
        manager = QRLoginManager()
        session_id = "s1"
        session = QRLoginSession(session_id=session_id)
        session.status = "waiting"
        manager.sessions[session_id] = session

        async def fake_poll_status(self, session: QRLoginSession) -> _FakeResponse:
            return _FakeResponse(
                cookies={"unb": "x", "_m_h5_tk": "tk", "_m_h5_tk_enc": "enc"},
                payload={"content": {"data": {"qrCodeStatus": "CONFIRMED"}}},
            )

        async def fake_bootstrap(self, session_id: str) -> None:
            s = manager.sessions[session_id]
            s.cookies["_m_h5_tk"] = "tk"
            s.cookies["_m_h5_tk_enc"] = "enc"

        async def run() -> None:
            with (
                patch.object(QRLoginManager, "_poll_status", new=fake_poll_status),
                patch.object(QRLoginManager, "_bootstrap_mtop_cookies", new=fake_bootstrap),
            ):
                await manager._monitor_qr_status(session_id)

        asyncio.run(run())
        self.assertEqual(session.status, "success")


if __name__ == "__main__":
    unittest.main()
