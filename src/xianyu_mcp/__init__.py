"""xianyu_mcp: 基于 XianYuApis 的闲鱼 MCP 服务。"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.0"


