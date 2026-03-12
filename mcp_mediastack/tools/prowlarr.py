"""Prowlarr tools – indexer management."""

from mcp_mediastack.helpers import _arr_get, _fmt
from mcp_mediastack.server import mcp


@mcp.tool()
async def get_prowlarr_status() -> str:
    """Get Prowlarr system status and indexer health."""
    status = await _arr_get("prowlarr", "/system/status")
    health = await _arr_get("prowlarr", "/health")
    try:
        indexers = await _arr_get("prowlarr", "/indexer")
        indexer_summary = [
            {"name": i.get("name"), "protocol": i.get("protocol"), "enable": i.get("enable")}
            for i in (indexers if isinstance(indexers, list) else [])
        ]
    except Exception:
        indexer_summary = "could not fetch indexers"
    return _fmt({"status": status, "health": health, "indexers": indexer_summary})
