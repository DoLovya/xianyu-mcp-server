from __future__ import annotations

import unittest

from xianyu_mcp.qr_login.models import QRLoginSession
from xianyu_mcp.qr_login.parsing import (
    extract_face_qr_content,
    extract_htoken,
    extract_login_form_data,
    extract_verify_modes_url,
)


class TestQRLoginParsing(unittest.TestCase):
    def test_extract_login_form_data(self) -> None:
        html = (
            '<html><script>window.viewData = {"loginFormData":{"appId":"1","a":2}};'
            "</script></html>"
        )
        data = extract_login_form_data(html)
        self.assertEqual(data["appId"], "1")
        self.assertEqual(data["a"], 2)
        self.assertEqual(data["umidTag"], "SERVER")

    def test_extract_htoken(self) -> None:
        html = "https://x.test/iv/mini/normal_validate.htm?htoken=abc_DEF-123&x=1"
        self.assertEqual(extract_htoken(html), "abc_DEF-123")

    def test_extract_verify_modes_url_append_umidfg(self) -> None:
        html = (
            'window.location.href="https://passport.goofish.com/iv/mini/verify_modes.htm?x=1&_umidfg="'
        )
        self.assertEqual(
            extract_verify_modes_url(html),
            "https://passport.goofish.com/iv/mini/verify_modes.htm?x=1&_umidfg=1",
        )

    def test_extract_face_qr_content(self) -> None:
        html = 'new Qrcode({ text: "https://example.com/q?x=1" })'
        self.assertEqual(extract_face_qr_content(html), "https://example.com/q?x=1")


class TestQRLoginSession(unittest.TestCase):
    def test_is_expired(self) -> None:
        s = QRLoginSession(session_id="1", created_time=10.0, expire_time=5.0)
        self.assertFalse(s.is_expired(now=14.9))
        self.assertTrue(s.is_expired(now=15.1))

    def test_to_public_dict(self) -> None:
        s = QRLoginSession(session_id="1")
        s.qr_data_url = "data:image/png;base64,xxx"
        d = s.to_public_dict()
        self.assertEqual(d["session_id"], "1")
        self.assertIn("status", d)
        self.assertIn("qr_data_url", d)


if __name__ == "__main__":
    unittest.main()
