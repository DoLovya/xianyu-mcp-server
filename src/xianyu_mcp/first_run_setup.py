from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .qr_login.manager import QRLoginManager


@dataclass
class FirstRunSetupState:
    session_id: str = ""
    status: str = "idle"
    local_url: str = ""
    qr_data_url: str = ""
    verification_url: str = ""
    face_qr_data_url: str = ""
    error_message: str = ""
    env_written: bool = False
    updated_at: float = 0.0


def _truthy_env(value: str) -> bool:
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def _dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _write_env_cookie(env_path: Path, cookie_str: str) -> None:
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    value = f'XIANYU_COOKIE="{cookie_str}"'
    out_lines: list[str] = []
    updated = False
    for line in lines:
        if line.startswith("XIANYU_COOKIE="):
            out_lines.append(value)
            updated = True
        else:
            out_lines.append(line)
    if not updated:
        out_lines.append(value)

    env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


class FirstRunSetup:
    def __init__(
        self,
        *,
        repo_root: Path,
        get_qr_login: Callable[[], QRLoginManager],
        load_cookie_str: Callable[[], str],
    ) -> None:
        self._repo_root = repo_root
        self._get_qr_login = get_qr_login
        self._load_cookie_str = load_cookie_str

        self._lock = threading.Lock()
        self._state = FirstRunSetupState()

        self._server: ThreadingHTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._orchestrator_thread: threading.Thread | None = None

    def enabled(self) -> bool:
        return _truthy_env(os.environ.get("XIANYU_SETUP_ENABLED", "1"))

    def auto_open_browser(self) -> bool:
        return _truthy_env(os.environ.get("XIANYU_SETUP_AUTO_OPEN", "1"))

    def auto_write_env(self) -> bool:
        return _truthy_env(os.environ.get("XIANYU_SETUP_AUTO_WRITE_ENV", "1"))

    def ensure_started(self) -> None:
        if not self.enabled():
            return
        if self._load_cookie_str():
            return
        with self._lock:
            if self._orchestrator_thread and self._orchestrator_thread.is_alive():
                return
            t = threading.Thread(target=self._run_orchestrator, name="xianyu-first-run-setup", daemon=True)
            self._orchestrator_thread = t
            t.start()

    def get_state_payload(self) -> dict[str, Any]:
        with self._lock:
            st = self._state
            return {
                "success": False,
                "requires_login": True,
                "session_id": st.session_id,
                "status": st.status,
                "local_url": st.local_url,
                "qr_data_url": st.qr_data_url,
                "verification_url": st.verification_url,
                "face_qr_data_url": st.face_qr_data_url,
                "error_message": st.error_message,
                "env_written": st.env_written,
            }

    def dump_state_payload(self) -> str:
        return _dump_json(self.get_state_payload())

    def _set_state(self, **kwargs: Any) -> None:
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._state, k):
                    setattr(self._state, k, v)
            self._state.updated_at = time.time()

    def _start_http_server(self) -> None:
        if self._server is not None:
            return

        setup = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def _write(self, status: int, content_type: str, body: bytes) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                if self.path.startswith("/status"):
                    body = _dump_json(setup.get_state_payload()).encode("utf-8")
                    self._write(HTTPStatus.OK, "application/json; charset=utf-8", body)
                    return
                if self.path != "/" and not self.path.startswith("/?"):
                    self._write(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"not found")
                    return

                html = setup._render_html().encode("utf-8")
                self._write(HTTPStatus.OK, "text/html; charset=utf-8", html)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server = server
        port = int(server.server_address[1])
        local_url = f"http://127.0.0.1:{port}/"
        self._set_state(local_url=local_url)
        t = threading.Thread(target=server.serve_forever, name="xianyu-first-run-web", daemon=True)
        self._server_thread = t
        t.start()

        if self.auto_open_browser():
            webbrowser.open(local_url)

    def _render_html(self) -> str:
        return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>闲鱼 MCP 首次配置</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial; margin: 24px; }
    .row { display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap; }
    .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; width: 360px; }
    .muted { color: #6b7280; font-size: 14px; }
    img { max-width: 100%; height: auto; }
    code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <h2>闲鱼 MCP 首次配置</h2>
  <div class="muted">扫码登录后会自动写入 <code>.env</code> 的 <code>XIANYU_COOKIE</code>。</div>
  <div class="row" style="margin-top: 16px;">
    <div class="card">
      <div><b>状态</b>: <span id="status">initializing</span></div>
      <div class="muted" id="session"></div>
      <div style="margin-top: 12px;">
        <img id="qr" alt="qr" />
      </div>
    </div>
    <div class="card">
      <div><b>验证入口</b></div>
      <div class="muted" id="verifyHint">无</div>
      <div style="margin-top: 12px;">
        <a id="verifyLink" target="_blank" rel="noreferrer"></a>
      </div>
      <div style="margin-top: 12px;">
        <img id="faceqr" alt="faceqr" />
      </div>
    </div>
  </div>
  <script>
    async function tick() {
      const res = await fetch("/status", { cache: "no-store" });
      const st = await res.json();
      document.getElementById("status").textContent = st.status || "unknown";
      document.getElementById("session").textContent = st.session_id ? ("session_id: " + st.session_id) : "";
      const qr = document.getElementById("qr");
      if (st.qr_data_url) qr.src = st.qr_data_url;
      const verifyHint = document.getElementById("verifyHint");
      const verifyLink = document.getElementById("verifyLink");
      if (st.verification_url) {
        verifyHint.textContent = "需要验证";
        verifyLink.textContent = st.verification_url;
        verifyLink.href = st.verification_url;
      } else {
        verifyHint.textContent = "无";
        verifyLink.textContent = "";
        verifyLink.href = "";
      }
      const faceqr = document.getElementById("faceqr");
      if (st.face_qr_data_url) faceqr.src = st.face_qr_data_url;
    }
    tick();
    setInterval(tick, 1000);
  </script>
</body>
</html>
"""

    def _run_orchestrator(self) -> None:
        self._set_state(status="initializing")
        self._start_http_server()

        qr_login = self._get_qr_login()
        last_opened_verification_url = ""
        try:
            result = asyncio.run(qr_login.generate())
        except Exception as e:
            self._set_state(status="error", error_message=type(e).__name__)
            return

        if not result.get("success"):
            self._set_state(status="error", error_message=str(result.get("error_message") or "generate_failed"))
            return

        session_id = str(result.get("session_id") or "")
        qr_data_url = str(result.get("qr_data_url") or "")
        self._set_state(session_id=session_id, qr_data_url=qr_data_url, status=str(result.get("status") or "waiting"))

        while True:
            if self._load_cookie_str():
                self._set_state(status="done")
                return

            status_info = qr_login.get_status(session_id)
            self._set_state(
                status=str(status_info.get("status") or ""),
                verification_url=str(status_info.get("verification_url") or ""),
                face_qr_data_url=str(status_info.get("face_qr_data_url") or ""),
                error_message=str(status_info.get("error_message") or ""),
            )

            status = str(status_info.get("status") or "")
            verification_url = str(status_info.get("verification_url") or "")
            if (
                status == "verification_required"
                and verification_url
                and verification_url != last_opened_verification_url
                and self.auto_open_browser()
            ):
                webbrowser.open(verification_url)
                last_opened_verification_url = verification_url
            if status == "success":
                cookie_info = qr_login.get_cookie(session_id)
                cookie_str = str(cookie_info.get("cookie") or "")
                if self.auto_write_env() and cookie_str and "_m_h5_tk=" in cookie_str:
                    _write_env_cookie(self._repo_root / ".env", cookie_str)
                    self._set_state(env_written=True)
                self._set_state(status="done")
                return
            if status in {"expired", "cancelled", "error"}:
                return

            time.sleep(1.0)
