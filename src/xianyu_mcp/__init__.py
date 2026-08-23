"""xianyu_mcp: 基于 XianYuApis 的闲鱼 MCP 服务（xianyu-mcp-server 官方包）。"""

from importlib.metadata import PackageNotFoundError, version as _version

__version__ = "0.0.0"
for _pkg in ("xianyu-mcp-server", __name__):
    try:
        __version__ = _version(_pkg)
        break
    except PackageNotFoundError:
        continue


