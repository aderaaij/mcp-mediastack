"""qBittorrent tools – torrent download management."""

import httpx

from mcp_mediastack.helpers import _fmt, _human_bytes, _url
from mcp_mediastack.server import (
    QBITTORRENT_PASS,
    QBITTORRENT_PORT,
    QBITTORRENT_USER,
    TIMEOUT,
    mcp,
)

# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_qbittorrent_status() -> str:
    """Get qBittorrent transfer info and active torrents."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        login_resp = await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
            data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
        )
        if login_resp.text.strip() != "Ok.":
            return f"Login failed: {login_resp.text}"

        info = (await client.get(_url(QBITTORRENT_PORT, "/api/v2/transfer/info"))).json()

        torrents = (
            await client.get(
                _url(QBITTORRENT_PORT, "/api/v2/torrents/info"),
                params={"filter": "active", "limit": "30"},
            )
        ).json()

        summary = []
        for t in torrents:
            summary.append(
                {
                    "name": t.get("name"),
                    "hash": t.get("hash"),
                    "state": t.get("state"),
                    "progress": f"{t.get('progress', 0) * 100:.1f}%",
                    "size": _human_bytes(t.get("size", 0)),
                    "dlspeed": _human_bytes(t.get("dlspeed", 0)) + "/s",
                    "upspeed": _human_bytes(t.get("upspeed", 0)) + "/s",
                    "eta": t.get("eta"),
                    "ratio": f"{t.get('ratio', 0):.2f}",
                    "category": t.get("category"),
                }
            )

        return _fmt(
            {
                "transfer": {
                    "dl_info_speed": _human_bytes(info.get("dl_info_speed", 0)) + "/s",
                    "up_info_speed": _human_bytes(info.get("up_info_speed", 0)) + "/s",
                    "dl_info_data": _human_bytes(info.get("dl_info_data", 0)),
                    "up_info_data": _human_bytes(info.get("up_info_data", 0)),
                    "connection_status": info.get("connection_status"),
                },
                "active_torrents": summary,
            }
        )


@mcp.tool()
async def get_qbittorrent_torrents(filter: str = "all", limit: int = 50) -> str:
    """List qBittorrent torrents. Filter: all, downloading, seeding, completed, paused, active, stalled."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
            data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
        )
        torrents = (
            await client.get(
                _url(QBITTORRENT_PORT, "/api/v2/torrents/info"),
                params={"filter": filter, "limit": str(limit)},
            )
        ).json()

        summary = []
        for t in torrents:
            summary.append(
                {
                    "name": t.get("name"),
                    "hash": t.get("hash"),
                    "state": t.get("state"),
                    "progress": f"{t.get('progress', 0) * 100:.1f}%",
                    "size": _human_bytes(t.get("size", 0)),
                    "ratio": f"{t.get('ratio', 0):.2f}",
                    "category": t.get("category"),
                    "added_on": t.get("added_on"),
                }
            )
        return _fmt({"count": len(summary), "torrents": summary})


# ---------------------------------------------------------------------------
# Action tools
# ---------------------------------------------------------------------------


async def _qbt_client() -> httpx.AsyncClient:
    """Create an authenticated qBittorrent client."""
    client = httpx.AsyncClient(timeout=TIMEOUT)
    await client.post(
        _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
        data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
    )
    return client


@mcp.tool()
async def qbittorrent_pause_torrents(hashes: str = "all") -> str:
    """Pause torrents. Use 'all' to pause everything, or a specific hash (from get_qbittorrent_torrents)."""
    async with await _qbt_client() as client:
        resp = await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/pause"),
            data={"hashes": hashes},
        )
        return _fmt({"action": "pause", "hashes": hashes, "status": resp.status_code})


@mcp.tool()
async def qbittorrent_resume_torrents(hashes: str = "all") -> str:
    """Resume torrents. Use 'all' to resume everything, or a specific hash."""
    async with await _qbt_client() as client:
        resp = await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/resume"),
            data={"hashes": hashes},
        )
        return _fmt({"action": "resume", "hashes": hashes, "status": resp.status_code})


@mcp.tool()
async def qbittorrent_delete_torrents(hashes: str, delete_files: bool = False) -> str:
    """Delete torrents by hash. Set delete_files=True to also remove downloaded data. Use '|' to separate multiple hashes."""
    async with await _qbt_client() as client:
        resp = await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/delete"),
            data={"hashes": hashes, "deleteFiles": str(delete_files).lower()},
        )
        return _fmt({"action": "delete", "hashes": hashes, "deletedFiles": delete_files, "status": resp.status_code})


@mcp.tool()
async def qbittorrent_reannounce_torrents(hashes: str = "all") -> str:
    """Force re-announce torrents to trackers. Useful for stalled torrents. Use 'all' or a specific hash."""
    async with await _qbt_client() as client:
        resp = await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/reannounce"),
            data={"hashes": hashes},
        )
        return _fmt({"action": "reannounce", "hashes": hashes, "status": resp.status_code})
