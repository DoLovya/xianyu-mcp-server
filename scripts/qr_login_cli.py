from __future__ import annotations

import asyncio
import base64
import subprocess
from pathlib import Path

from xianyu_mcp.qr_login.manager import QRLoginManager


def save_data_url_png(data_url: str, path: Path) -> bool:
    prefix = "base64,"
    i = data_url.find(prefix)
    if i < 0:
        return False
    b64 = data_url[i + len(prefix) :]
    path.write_bytes(base64.b64decode(b64))
    return True


async def main() -> None:
    manager = QRLoginManager()
    result = await manager.generate()
    if not result.get("success"):
        print(result)
        return

    session_id = result["session_id"]
    print("SESSION_ID", session_id)
    qr_data_url = result.get("qr_data_url", "")
    print("QR_DATA_URL", qr_data_url)
    if qr_data_url:
        out_path = Path("/tmp/xianyu_qr_login.png")
        if save_data_url_png(qr_data_url, out_path):
            print("QR_PNG", str(out_path))
            subprocess.run(["open", str(out_path)], check=False)

    last_status: str | None = None
    last_verification_url: str | None = None
    opened_face_qr = False
    for _ in range(600):
        status_info = manager.get_status(session_id)
        status = status_info.get("status")
        if status != last_status:
            print("STATUS", status)
            last_status = status

        if status == "verification_required":
            if status_info.get("verification_url"):
                verification_url = str(status_info["verification_url"])
                print("VERIFICATION_URL", verification_url)
                if verification_url != last_verification_url:
                    subprocess.run(["open", verification_url], check=False)
                    last_verification_url = verification_url
            if status_info.get("face_qr_data_url"):
                face_qr_data_url = str(status_info["face_qr_data_url"])
                print("FACE_QR_DATA_URL", face_qr_data_url)
                if not opened_face_qr:
                    face_path = Path("/tmp/xianyu_qr_face_verify.png")
                    if save_data_url_png(face_qr_data_url, face_path):
                        print("FACE_QR_PNG", str(face_path))
                        subprocess.run(["open", str(face_path)], check=False)
                        opened_face_qr = True

        if status in {"success", "error", "expired", "cancelled"}:
            break

        await asyncio.sleep(1)

    final_status = manager.get_status(session_id)
    if final_status.get("status") == "success":
        cookie_info = manager.get_cookie(session_id)
        print("UNB", cookie_info.get("unb", ""))
        print("COOKIE", cookie_info.get("cookie", ""))
        return

    print("FINAL", final_status)


if __name__ == "__main__":
    asyncio.run(main())
