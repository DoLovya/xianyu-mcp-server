from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from tools.xianyu_api_tools import XianYuApiTools

_MCP_ROOT = Path(__file__).resolve().parent
load_dotenv(_MCP_ROOT / ".env")


def _load_cookie_str() -> str:
    cookie_str = os.environ.get("XIANYU_COOKIE", "").strip()
    if cookie_str:
        return cookie_str

    cookie_file = os.environ.get("XIANYU_COOKIE_FILE", "").strip()
    if cookie_file:
        return Path(cookie_file).expanduser().read_text(encoding="utf-8").strip()

    return ""


mcp = FastMCP(
    "XianYu APIs",
    instructions=(
        "基于 XianYuApis 的闲鱼 MCP 服务。"
        "当前支持登录态校验、token 刷新、商品详情查询、主动发文本消息、主动发图片消息、会话历史查询。"
        "调用前请先在 .env 中配置 XIANYU_COOKIE 或 XIANYU_COOKIE_FILE。"
    ),
)

_tools: XianYuApiTools | None = None


def _get_tools() -> XianYuApiTools:
    global _tools
    if _tools is None:
        _tools = XianYuApiTools(cookie_str=_load_cookie_str())
    return _tools


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def validate_login() -> str:
    """校验当前 Cookie 对应的闲鱼登录态，并尝试获取 accessToken。"""
    return _get_tools().validate_login()


@mcp.tool()
def refresh_login() -> str:
    """刷新当前登录态对应的 token/cookie。"""
    return _get_tools().refresh_login()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def get_item_detail(item_id: str) -> str:
    """获取指定闲鱼商品详情。

    Args:
        item_id: 商品 ID，例如 1001160709960。
    """
    return _get_tools().get_item_detail(item_id=item_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_conversation_messages(cid: str, max_items: int = 50) -> str:
    """读取指定会话的历史消息。

    Args:
        cid: 会话 ID，不带 @goofish 后缀。
        max_items: 最多返回多少条最近消息，默认 50。
    """
    return await _get_tools().list_conversation_messages(cid=cid, max_items=max_items)


@mcp.tool()
async def send_text_message(to_user_id: str, item_id: str, text: str) -> str:
    """向指定用户主动发送文本消息。

    Args:
        to_user_id: 对方用户 ID。
        item_id: 建聊时绑定的商品 ID。
        text: 要发送的文本内容。
    """
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
    return await _get_tools().send_image_message(
        to_user_id=to_user_id,
        item_id=item_id,
        image=image,
    )


if __name__ == "__main__":
    import sys

    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
        print("XianYuApis MCP Server 启动中（HTTP 模式）...")
        print("监听地址: http://localhost:8000/mcp")
        print("按 Ctrl+C 停止服务器\n")

    mcp.run(transport=transport)
