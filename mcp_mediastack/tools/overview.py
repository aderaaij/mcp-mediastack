"""System overview tool – aggregated status across all services."""

import httpx

from mcp_mediastack.helpers import _arr_get, _fmt, _get, _human_bytes, _url
from mcp_mediastack.server import (
    GLUETUN_PORT,
    QBITTORRENT_PASS,
    QBITTORRENT_PORT,
    QBITTORRENT_USER,
    SABNZBD_API_KEY,
    SABNZBD_PORT,
    TIMEOUT,
    mcp,
)


@mcp.tool()
async def get_system_overview() -> str:
    """Get a quick overview of all services – VPN status, download speeds, queue sizes, and health."""
    overview = {}

    # VPN
    try:
        ip_data = await _get(GLUETUN_PORT, "/v1/publicip/ip")
        overview["vpn"] = {"status": "connected", "ip": ip_data}
    except Exception as e:
        overview["vpn"] = {"status": "error", "detail": str(e)}

    # Sonarr
    try:
        health = await _arr_get("sonarr", "/health")
        queue = await _arr_get("sonarr", "/queue?pageSize=1")
        overview["sonarr"] = {
            "healthy": len(health) == 0 if isinstance(health, list) else "unknown",
            "queueSize": queue.get("totalRecords", 0) if isinstance(queue, dict) else "unknown",
            "issues": len(health) if isinstance(health, list) else 0,
        }
    except Exception as e:
        overview["sonarr"] = {"status": "error", "detail": str(e)}

    # Radarr
    try:
        health = await _arr_get("radarr", "/health")
        queue = await _arr_get("radarr", "/queue?pageSize=1")
        overview["radarr"] = {
            "healthy": len(health) == 0 if isinstance(health, list) else "unknown",
            "queueSize": queue.get("totalRecords", 0) if isinstance(queue, dict) else "unknown",
            "issues": len(health) if isinstance(health, list) else 0,
        }
    except Exception as e:
        overview["radarr"] = {"status": "error", "detail": str(e)}

    # SABnzbd
    try:
        data = await _get(SABNZBD_PORT, "/api", params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue"})
        q = data.get("queue", {}) if isinstance(data, dict) else {}
        overview["sabnzbd"] = {
            "status": q.get("status"),
            "speed": q.get("speed"),
            "queueSize": q.get("noofslots"),
            "paused": q.get("paused"),
        }
    except Exception as e:
        overview["sabnzbd"] = {"status": "error", "detail": str(e)}

    # qBittorrent
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            await client.post(
                _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
                data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
            )
            info = (await client.get(_url(QBITTORRENT_PORT, "/api/v2/transfer/info"))).json()
            overview["qbittorrent"] = {
                "connection_status": info.get("connection_status"),
                "dl_speed": _human_bytes(info.get("dl_info_speed", 0)) + "/s",
                "up_speed": _human_bytes(info.get("up_info_speed", 0)) + "/s",
            }
    except Exception as e:
        overview["qbittorrent"] = {"status": "error", "detail": str(e)}

    # Prowlarr
    try:
        health = await _arr_get("prowlarr", "/health")
        overview["prowlarr"] = {
            "healthy": len(health) == 0 if isinstance(health, list) else "unknown",
            "issues": len(health) if isinstance(health, list) else 0,
        }
    except Exception as e:
        overview["prowlarr"] = {"status": "error", "detail": str(e)}

    # Readarr
    try:
        health = await _arr_get("readarr", "/health")
        overview["readarr"] = {
            "healthy": len(health) == 0 if isinstance(health, list) else "unknown",
            "issues": len(health) if isinstance(health, list) else 0,
        }
    except Exception as e:
        overview["readarr"] = {"status": "error", "detail": str(e)}

    return _fmt(overview)
