from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYXIANYU_ROOT = _REPO_ROOT / "third_party" / "pyxianyu"
sys.path.insert(0, str(_PYXIANYU_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "src"))


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self):
        self.user_page_nav_url = "https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/"
        self.captured = {}

    def build_mtop_params(self, api, spm_cnt, spm_pre, log_id, v="1.0"):
        return {"api": api, "spm_cnt": spm_cnt, "spm_pre": spm_pre, "log_id": log_id, "v": v}

    def post_json(self, url, params, data_val, headers=None, verify=None):
        self.captured = {
            "url": url,
            "params": dict(params),
            "data_val": data_val,
        }
        return _FakeResponse({"api": params.get("api"), "ret": ["SUCCESS::调用成功"], "data": {}})

    def parse_json_response(self, response, *, api_name=None):
        return response.json()

    def ensure_api_success(self, payload, *, api_name=None):
        return payload


class _FakeGuardrails:
    def run_read(self, fn):
        return fn()


class _FakeUserApi:
    def get_user_page_nav(self):
        return {
            "ret": ["SUCCESS::调用成功"],
            "data": {"userInfo": {"userId": 222, "nick": "tester", "avatarUrl": "https://example.com/a.png"}},
        }


class TestUserProfile(unittest.TestCase):
    def test_user_api_builds_request(self) -> None:
        from pyxianyu.apis.user_api import UserApi

        client = _FakeClient()
        api = UserApi(client)
        api.get_user_page_nav()
        self.assertEqual(client.captured["url"], client.user_page_nav_url)
        self.assertEqual(client.captured["params"]["api"], "mtop.idle.web.user.page.nav")
        self.assertEqual(client.captured["data_val"], "{}")

    def test_tools_output_shape(self) -> None:
        from xianyu_mcp.tools.xianyu_api_tools import XianYuApiTools

        tools = XianYuApiTools(cookie_str="dummy=1")
        tools._guardrails = _FakeGuardrails()
        tools._get_user_api = lambda: _FakeUserApi()

        got = json.loads(tools.get_my_profile())
        self.assertEqual(got["success"], True)
        self.assertIn("raw", got)
        self.assertIn("profile", got)
        self.assertEqual(got["profile"]["user_id"], 222)
        self.assertEqual(got["profile"]["nick"], "tester")


if __name__ == "__main__":
    unittest.main()
