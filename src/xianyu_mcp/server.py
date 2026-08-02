from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .first_run_setup import FirstRunSetup
from .qr_login.manager import QRLoginManager
from .qr_login.utils import dump_json
from .tools.xianyu_api_tools import XianYuApiTools


def _truthy(value: str) -> bool:
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def _resolve_repo_root() -> Path:
    env_root = os.environ.get("XIANYU_REPO_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()

    cwd = Path.cwd().resolve()
    for p in (cwd, *cwd.parents):
        if (p / "pyproject.toml").is_file() and (p / "src" / "xianyu_mcp").is_dir():
            return p

    return Path(__file__).resolve().parents[2]


def _configure_logging(repo_root: Path) -> None:
    level = os.environ.get("XIANYU_LOG_LEVEL", "INFO").strip().upper() or "INFO"
    try:
        logger.remove()
    except Exception:
        pass

    logger.add(sys.stderr, level=level, backtrace=False, diagnose=False)

    if not _truthy(os.environ.get("XIANYU_LOG_TO_FILE", "0")):
        return

    log_file = os.environ.get("XIANYU_LOG_FILE", "").strip()
    try:
        if log_file:
            path = Path(log_file).expanduser()
            if not path.is_absolute():
                path = (repo_root / path).resolve()
        else:
            path = (repo_root / ".logs" / "xianyu_mcp.log").resolve()

        path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(path),
            level=level,
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )
        logger.info("xianyu_mcp log_file={}", str(path))
    except Exception as e:
        logger.warning("xianyu_mcp log_file_failed error={}", type(e).__name__)


_REPO_ROOT = _resolve_repo_root()
load_dotenv(_REPO_ROOT / ".env")
_configure_logging(_REPO_ROOT)
logger.info("xianyu_mcp repo_root={}", str(_REPO_ROOT))


def _load_cookie_str() -> str:
    # Re-read .env on every tool invocation so a long-lived MCP process can
    # pick up newly updated credentials without requiring a manual restart.
    load_dotenv(_REPO_ROOT / ".env", override=False)

    cookie_str = os.environ.get("XIANYU_COOKIE", "").strip()
    if cookie_str:
        return cookie_str

    cookie_file = os.environ.get("XIANYU_COOKIE_FILE", "").strip()
    if cookie_file:
        cookie_path = Path(cookie_file).expanduser()
        if not cookie_path.is_absolute():
            cookie_path = (_REPO_ROOT / cookie_path).resolve()
        return cookie_path.read_text(encoding="utf-8").strip()

    return ""


mcp = FastMCP(
    "XianYu APIs",
    instructions=(
        "基于 pyxianyu 的闲鱼 MCP 服务。"
        "当前支持登录态校验、token 刷新、商品搜索、商品详情查询、商品编辑详情查询、商品编辑、我的商品列表查询、商品下架、商品重新上架、发布实体商品、媒体上传、会话列表查询、主动发文本消息、主动发图片消息、会话历史查询。"
        "大部分工具调用前请先在 .env 中配置 XIANYU_COOKIE 或 XIANYU_COOKIE_FILE；如无 Cookie，可先使用 qr_login_* 工具扫码获取。"
    ),
)

_tools: XianYuApiTools | None = None
_qr_login: QRLoginManager | None = None
_first_run_setup: FirstRunSetup | None = None


def _get_tools() -> XianYuApiTools:
    global _tools
    cookie_str = _load_cookie_str()
    if _tools is None or _tools.cookie_str != cookie_str:
        _tools = XianYuApiTools(cookie_str=cookie_str)
    return _tools


def _get_qr_login() -> QRLoginManager:
    global _qr_login
    if _qr_login is None:
        _qr_login = QRLoginManager()
    return _qr_login


def _get_first_run_setup() -> FirstRunSetup:
    global _first_run_setup
    if _first_run_setup is None:
        _first_run_setup = FirstRunSetup(
            repo_root=_REPO_ROOT,
            get_qr_login=_get_qr_login,
            load_cookie_str=_load_cookie_str,
        )
    return _first_run_setup


def _maybe_requires_login_payload() -> dict[str, Any] | None:
    if _load_cookie_str():
        return None
    setup = _get_first_run_setup()
    setup.ensure_started()
    return setup.get_state_payload()


if _truthy(os.environ.get("XIANYU_SETUP_AUTOSTART", "1")):
    _get_first_run_setup().ensure_started()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def validate_login() -> str:
    """校验当前 Cookie 对应的闲鱼登录态，并尝试获取 accessToken。"""
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().validate_login()


@mcp.tool()
def refresh_login() -> str:
    """刷新当前登录态对应的 token/cookie。"""
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().refresh_login()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_item_detail(item_id: str) -> str:
    """获取指定闲鱼商品详情。

    Args:
        item_id: 商品 ID，例如 1001160709960。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().get_item_detail(item_id=item_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def search_items(
    keyword: str,
    page_number: int = 1,
    rows_per_page: int = 20,
    sort_field: str = "",
    sort_value: str = "",
) -> str:
    """按关键词搜索闲鱼商品（PC Web 搜索接口）。

    Args:
        keyword: 搜索关键词。
        page_number: 页码，从 1 开始。
        rows_per_page: 单页条数，默认 20，当前会限制在 1 到 50 之间。
        sort_field: 排序字段，例如 create。
        sort_value: 排序值，例如 desc。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().search_items(
        keyword=keyword,
        page_number=page_number,
        rows_per_page=rows_per_page,
        sort_field=sort_field,
        sort_value=sort_value,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_item_edit_detail(item_id: str) -> str:
    """获取指定商品在 PC 编辑页的编辑详情数据。

    Args:
        item_id: 商品 ID，例如 1048303755272。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().get_item_edit_detail(item_id=item_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_my_items(page_size: int = 20) -> str:
    """读取当前登录账号名下的全部商品列表，并自动翻页聚合。

    Args:
        page_size: 单页拉取条数，默认 20，当前会限制在 1 到 50 之间。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().list_my_items(page_size=page_size)


@mcp.tool()
def downshelf_item(item_id: str) -> str:
    """下架当前登录账号名下的指定商品。

    Args:
        item_id: 商品 ID，例如 897705472395。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().downshelf_item(item_id=item_id)


@mcp.tool()
def reshelf_item(item_id: str, source_id: str = "") -> str:
    """通过 PC 编辑重发布链路重新上架指定商品。

    Args:
        item_id: 商品 ID，例如 1048303755272。
        source_id: 可选。转发给 `mtop.idle.pc.idleitem.edit` 的 sourceId，留空时默认回退到 item_id。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().reshelf_item(item_id=item_id, source_id=source_id)


@mcp.tool()
def edit_item(
    item_id: str,
    payload: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> str:
    """编辑指定商品信息（仅对支持 PC 编辑的实体商品有效）。

    Args:
        item_id: 商品 ID，例如 1048303755272。
        payload: 可选。直接编辑模式，完整 payload（与 overrides 互斥）。
        overrides: 可选。快速编辑模式，仅提供需要修改的字段（与 payload 互斥）。
    """
    payload2 = _maybe_requires_login_payload()
    if payload2:
        return dump_json(payload2)
    return _get_tools().edit_item(item_id=item_id, payload=payload, overrides=overrides)


@mcp.tool()
def publish_physical_item(title: str, price: str, desc: str, images: list[str]) -> str:
    """在闲鱼 PC 端发布全新的实体商品。支持自动上传图片并构造发布请求。

    Args:
        title: 商品标题。
        price: 商品价格（元，例如 "99.00"）。
        desc: 商品描述。
        images: 商品图片路径列表，支持本地绝对路径或 http/https URL，至少 1 张。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().publish_physical_item(
        title=title,
        price=price,
        desc=desc,
        images=images,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_conversations(max_items: int = 1000, include_hidden: bool = False) -> str:
    """读取当前账号最近会话列表。

    Args:
        max_items: 最多返回多少个会话，默认 1000，当前单次上限 1000。
        include_hidden: 是否包含已隐藏会话，默认 False。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return await _get_tools().list_conversations(
        max_items=max_items,
        include_hidden=include_hidden,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_conversation_messages(cid: str, max_items: int = 50) -> str:
    """读取指定会话的历史消息。

    Args:
        cid: 会话 ID，不带 @goofish 后缀。
        max_items: 最多返回多少条最近消息，默认 50。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return await _get_tools().list_conversation_messages(cid=cid, max_items=max_items)


@mcp.tool()
async def send_text_message(to_user_id: str, item_id: str, text: str) -> str:
    """向指定用户主动发送文本消息。

    Args:
        to_user_id: 对方用户 ID。
        item_id: 建聊时绑定的商品 ID。
        text: 要发送的文本内容。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return await _get_tools().send_text_message(
        to_user_id=to_user_id,
        item_id=item_id,
        text=text,
    )


@mcp.tool()
async def send_image_message(to_user_id: str, item_id: str, image: str) -> str:
    """向指定用户主动发送图片消息。

    Args:
        to_user_id: 对方用户 ID。
        item_id: 建聊时绑定的商品 ID。
        image: 本地图片绝对路径，或 http/https 图片地址。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return await _get_tools().send_image_message(
        to_user_id=to_user_id,
        item_id=item_id,
        image=image,
    )


@mcp.tool()
def upload_media(media: str) -> str:
    """上传本地文件或 URL 素材，并返回可复用的媒体 URL。

    Args:
        media: 本地文件绝对路径，或 http/https 媒体地址。
    """
    payload = _maybe_requires_login_payload()
    if payload:
        return dump_json(payload)
    return _get_tools().upload_media(media=media)


@mcp.tool()
async def qr_login_generate() -> str:
    """生成闲鱼扫码登录二维码（data-url），并返回 session_id 用于后续查询。"""
    result = await _get_qr_login().generate()
    return dump_json(result)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def qr_login_status(session_id: str) -> str:
    """查询扫码登录会话状态。"""
    return dump_json(_get_qr_login().get_status(session_id))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def qr_login_cookie(session_id: str) -> str:
    """在扫码登录成功后，获取该会话的完整 Cookie。"""
    return dump_json(_get_qr_login().get_cookie(session_id))


@mcp.tool()
def qr_login_save_env(session_id: str, env_path: str = ".env") -> str:
    """将扫码登录成功后的 Cookie 写入指定 env 文件（显式调用才会写入）。"""
    cookie_info = _get_qr_login().get_cookie(session_id)
    if cookie_info.get("success") is not True:
        return dump_json(cookie_info)

    cookie_str = str(cookie_info.get("cookie") or "")
    if "_m_h5_tk=" not in cookie_str:
        logger.warning(
            "qr_login_save_env missing_mtop_token session_id={} env_path={} cookie_len={}",
            session_id,
            env_path,
            len(cookie_str),
        )
        return dump_json(
            {
                "success": False,
                "status": "error",
                "message": "missing_mtop_token",
                "session_id": session_id,
            }
        )

    target = Path(env_path).expanduser()
    if not target.is_absolute():
        target = (_REPO_ROOT / target).resolve()

    logger.info(
        "qr_login_save_env writing session_id={} env_path={} cookie_len={} has_mtop_token={} has_x5sec={}",
        session_id,
        str(target),
        len(cookie_str),
        "_m_h5_tk=" in cookie_str and "_m_h5_tk_enc=" in cookie_str,
        "x5sec=" in cookie_str,
    )

    lines: list[str] = []
    if target.exists():
        raw = target.read_text(encoding="utf-8")
        lines = raw.splitlines()

    value = f'XIANYU_COOKIE="{cookie_str}"'
    updated = False
    out_lines: list[str] = []
    for line in lines:
        if line.startswith("XIANYU_COOKIE="):
            out_lines.append(value)
            updated = True
        else:
            out_lines.append(line)
    if not updated:
        out_lines.append(value)

    try:
        target.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    except Exception as e:
        logger.exception(
            "qr_login_save_env write_failed session_id={} env_path={} error={}",
            session_id,
            str(target),
            type(e).__name__,
        )
        return dump_json(
            {
                "success": False,
                "status": "error",
                "message": "write_failed",
                "session_id": session_id,
                "env_path": str(target),
                "error": type(e).__name__,
            }
        )
    return dump_json(
        {
            "success": True,
            "session_id": session_id,
            "status": "saved",
            "env_path": str(target),
            "has_mtop_token": "_m_h5_tk=" in cookie_str and "_m_h5_tk_enc=" in cookie_str,
            "has_x5sec": "x5sec=" in cookie_str,
        }
    )


def main() -> None:
    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
        print("XianYuApis MCP Server 启动中（HTTP 模式）...")
        print("监听地址: http://localhost:8000/mcp")
        print("按 Ctrl+C 停止服务器\n")

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
