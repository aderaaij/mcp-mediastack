"""Readarr tools – book/ebook management."""

from mcp_mediastack.helpers import _arr_get, _fmt, _human_bytes
from mcp_mediastack.server import mcp


@mcp.tool()
async def get_readarr_status() -> str:
    """Get Readarr system status and health."""
    status = await _arr_get("readarr", "/system/status")
    health = await _arr_get("readarr", "/health")
    return _fmt({"status": status, "health": health})


@mcp.tool()
async def get_readarr_queue() -> str:
    """Get Readarr download queue."""
    data = await _arr_get("readarr", "/queue?pageSize=50")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for item in records:
        items.append(
            {
                "title": item.get("title"),
                "status": item.get("status"),
                "size": _human_bytes(item.get("size", 0)),
                "sizeleft": _human_bytes(item.get("sizeleft", 0)),
                "timeleft": item.get("timeleft"),
                "downloadClient": item.get("downloadClient"),
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})
