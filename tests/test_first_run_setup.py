from __future__ import annotations

import json
import os
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from xianyu_mcp.first_run_setup import FirstRunSetup


class TestFirstRunSetupWeb(unittest.TestCase):
    def test_status_endpoint(self) -> None:
        with patch.dict(os.environ, {"XIANYU_SETUP_AUTO_OPEN": "0"}):
            setup = FirstRunSetup(
                repo_root=Path("/tmp"),
                get_qr_login=lambda: None,  # type: ignore[arg-type]
                load_cookie_str=lambda: "",
            )
            setup._set_state(session_id="s1", status="waiting", qr_data_url="data:image/png;base64,abc")
            setup._start_http_server()
            payload = setup.get_state_payload()
            local_url = str(payload["local_url"])
            with urllib.request.urlopen(local_url + "status") as resp:
                data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["session_id"], "s1")
            self.assertEqual(data["status"], "waiting")
            self.assertTrue(data["requires_login"])
            self.assertTrue(data["local_url"].startswith("http://127.0.0.1:"))

            if setup._server is not None:
                setup._server.shutdown()
                setup._server.server_close()


class TestServerRequiresLogin(unittest.TestCase):
    def test_validate_login_returns_requires_login(self) -> None:
        with patch.dict(
            os.environ,
            {"XIANYU_SETUP_AUTOSTART": "0", "XIANYU_SETUP_ENABLED": "0"},
        ):
            import importlib

            server = importlib.import_module("xianyu_mcp.server")
            with patch.object(server, "_load_cookie_str", return_value=""):
                result = json.loads(server.validate_login())
            self.assertFalse(result["success"])
            self.assertTrue(result["requires_login"])


if __name__ == "__main__":
    unittest.main()

