"""Bazarr tools – subtitle management."""

import os

from mcp_mediastack.helpers import _fmt, _get
from mcp_mediastack.server import SERVICES, mcp


@mcp.tool()
async def get_bazarr_status() -> str:
    """Get Bazarr system status and health."""
    api_key = os.environ.get("BAZARR_API_KEY", "")
    port = SERVICES["bazarr"]["port"]
    status = await _get(port, "/api/system/status", headers={"X-API-KEY": api_key})
    health = await _get(port, "/api/system/health", headers={"X-API-KEY": api_key})
    return _fmt({"status": status, "health": health})


@mcp.tool()
async def get_bazarr_wanted(page_size: int = 20) -> str:
    """Get Bazarr wanted/missing subtitles."""
    api_key = os.environ.get("BAZARR_API_KEY", "")
    port = SERVICES["bazarr"]["port"]
    movies = await _get(port, f"/api/movies/wanted?length={page_size}", headers={"X-API-KEY": api_key})
    series = await _get(port, f"/api/episodes/wanted?length={page_size}", headers={"X-API-KEY": api_key})
    return _fmt({"wanted_movies": movies, "wanted_episodes": series})
