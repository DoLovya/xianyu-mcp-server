from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

QRLoginStatus = Literal[
    "waiting",
    "scanned",
    "verification_required",
    "success",
    "expired",
    "cancelled",
    "error",
]


@dataclass
class QRLoginSession:
    session_id: str
    status: QRLoginStatus = "waiting"
    created_time: float = field(default_factory=time.time)
    expire_time: float = 300.0
    params: dict[str, Any] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    qr_content: str | None = None
    qr_data_url: str | None = None
    unb: str | None = None
    verification_url: str | None = None
    face_qr_content: str | None = None
    face_qr_data_url: str | None = None
    error_message: str | None = None

    def is_expired(self, now: float | None = None) -> bool:
        ts = time.time() if now is None else float(now)
        return ts - self.created_time > float(self.expire_time)

    def to_public_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "session_id": self.session_id,
            "status": self.status,
            "is_expired": self.is_expired(),
            "has_mtop_token": bool(self.cookies.get("_m_h5_tk"))
            and bool(self.cookies.get("_m_h5_tk_enc")),
            "has_x5sec": bool(self.cookies.get("x5sec")),
        }
        if self.qr_data_url:
            data["qr_data_url"] = self.qr_data_url
        if self.verification_url:
            data["verification_url"] = self.verification_url
        if self.face_qr_data_url:
            data["face_qr_data_url"] = self.face_qr_data_url
        if self.error_message:
            data["message"] = self.error_message
        if self.status == "success" and self.unb:
            data["unb"] = self.unb
        return data
