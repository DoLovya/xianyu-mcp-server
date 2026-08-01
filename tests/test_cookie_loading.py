from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestCookieLoading(unittest.TestCase):
    def test_env_cookie_has_priority_over_dotenv(self) -> None:
        import importlib

        server = importlib.import_module("xianyu_mcp.server")

        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / ".env").write_text('XIANYU_COOKIE="from_dotenv"\n', encoding="utf-8")

            with patch.object(server, "_REPO_ROOT", repo):
                with patch.dict(os.environ, {"XIANYU_COOKIE": "from_env"}, clear=False):
                    got = server._load_cookie_str()

        self.assertEqual(got, "from_env")

    def test_cookie_file_is_used_when_env_cookie_empty(self) -> None:
        import importlib

        server = importlib.import_module("xianyu_mcp.server")

        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            cookie_path = repo / "cookie.txt"
            cookie_path.write_text("cookie_from_file", encoding="utf-8")
            (repo / ".env").write_text("", encoding="utf-8")

            with patch.object(server, "_REPO_ROOT", repo):
                with patch.dict(
                    os.environ,
                    {"XIANYU_COOKIE": "", "XIANYU_COOKIE_FILE": str(cookie_path)},
                    clear=False,
                ):
                    got = server._load_cookie_str()

        self.assertEqual(got, "cookie_from_file")


if __name__ == "__main__":
    unittest.main()

