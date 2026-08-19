from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYXIANYU_ROOT = _REPO_ROOT / "third_party" / "pyxianyu"
sys.path.insert(0, str(_PYXIANYU_ROOT))


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self):
        self.item_search_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/"
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


class TestItemSearch(unittest.TestCase):
    def test_search_api_builds_request_data(self) -> None:
        from pyxianyu.apis.search_api import SearchApi

        client = _FakeClient()
        api = SearchApi(client)
        api.search_items(
            "iPhone 13",
            page_number=2,
            rows_per_page=30,
            sort_field="create",
            sort_value="desc",
            from_filter=True,
        )
        got = json.loads(client.captured["data_val"])
        self.assertEqual(got["keyword"], "iPhone 13")
        self.assertEqual(got["pageNumber"], 2)
        self.assertEqual(got["rowsPerPage"], 30)
        self.assertEqual(got["sortField"], "create")
        self.assertEqual(got["sortValue"], "desc")
        self.assertEqual(got["fromFilter"], True)

    def test_missing_m_h5_tk_raises(self) -> None:
        from pyxianyu.core.client import XianyuClient
        from pyxianyu.core.exceptions import XianyuConfigError

        client = XianyuClient(cookies={}, device_id="dummy")
        params = client.build_mtop_params(
            api="mtop.taobao.idlemtopsearch.pc.search",
            spm_cnt="a21ybx.search.0.0",
            spm_pre="a21ybx.search.searchInput.0",
            log_id="xianyu_item_search",
        )
        with self.assertRaises(XianyuConfigError):
            client.build_signed_form(params, "{}")


if __name__ == "__main__":
    unittest.main()

