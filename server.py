"""MCP server for monitoring a Synology NAS media stack."""

import os
import json
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")  # "stdio" or "sse"
MCP_PORT = int(os.environ.get("MCP_PORT", 8888))

mcp = FastMCP("mediastack", host="0.0.0.0", port=MCP_PORT)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NAS_HOST = os.environ.get("NAS_HOST", "192.168.1.100")

SERVICES = {
    "sonarr": {
        "port": int(os.environ.get("SONARR_PORT", 8989)),
        "api_key": os.environ.get("SONARR_API_KEY", ""),
    },
    "radarr": {
        "port": int(os.environ.get("RADARR_PORT", 7878)),
        "api_key": os.environ.get("RADARR_API_KEY", ""),
    },
    "prowlarr": {
        "port": int(os.environ.get("PROWLARR_PORT", 9696)),
        "api_key": os.environ.get("PROWLARR_API_KEY", ""),
        "api_version": "v1",
    },
    "readarr": {
        "port": int(os.environ.get("READARR_PORT", 8787)),
        "api_key": os.environ.get("READARR_API_KEY", ""),
        "api_version": "v1",
    },
    "bazarr": {
        "port": int(os.environ.get("BAZARR_PORT", 6767)),
        "api_key": os.environ.get("BAZARR_API_KEY", ""),
    },
}

SABNZBD_PORT = int(os.environ.get("SABNZBD_PORT", 8080))
SABNZBD_API_KEY = os.environ.get("SABNZBD_API_KEY", "")

QBITTORRENT_PORT = int(os.environ.get("QBITTORRENT_PORT", 8090))
QBITTORRENT_USER = os.environ.get("QBITTORRENT_USERNAME", "admin")
QBITTORRENT_PASS = os.environ.get("QBITTORRENT_PASSWORD", "adminadmin")

SEERR_PORT = int(os.environ.get("SEERR_PORT", 5055))
SEERR_API_KEY = os.environ.get("SEERR_API_KEY", "")

GLUETUN_PORT = int(os.environ.get("GLUETUN_PORT", 8005))

TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(port: int, path: str) -> str:
    return f"http://{NAS_HOST}:{port}{path}"


async def _get(port: int, path: str, headers: dict | None = None, params: dict | None = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if params:
            kwargs["params"] = params
        resp = await client.get(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _post(port: int, path: str, headers: dict | None = None, json_data: Any = None, params: dict | None = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if json_data is not None:
            kwargs["json"] = json_data
        if params:
            kwargs["params"] = params
        resp = await client.post(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _delete(port: int, path: str, headers: dict | None = None, params: dict | None = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if params:
            kwargs["params"] = params
        resp = await client.delete(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _put(port: int, path: str, headers: dict | None = None, json_data: Any = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.put(_url(port, path), headers=headers or {}, json=json_data)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _arr_get(service: str, path: str) -> dict | list | str:
    """GET request to an *arr service (Sonarr, Radarr, etc.)."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _get(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]})


async def _arr_post(service: str, path: str, json_data: Any = None) -> dict | list | str:
    """POST request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _post(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, json_data=json_data)


async def _arr_delete(service: str, path: str, params: dict | None = None) -> dict | list | str:
    """DELETE request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _delete(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, params=params)


async def _arr_put(service: str, path: str, json_data: Any = None) -> dict | list | str:
    """PUT request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _put(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, json_data=json_data)


def _fmt(data: Any) -> str:
    """Format data for display."""
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, default=str)
    return str(data)


def _human_bytes(b: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _se(season: Any, episode: Any) -> str:
    """Format season/episode as S01E02."""
    try:
        return f"S{int(season):02d}E{int(episode):02d}"
    except (TypeError, ValueError):
        return f"S{season}E{episode}"


# ---------------------------------------------------------------------------
# Tools – VPN / Gluetun
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_vpn_status() -> str:
    """Get VPN connection status from Gluetun – public IP, forwarded port, and connection details."""
    results = {}
    for endpoint in ["/v1/publicip/ip", "/v1/openvpn/status"]:
        try:
            results[endpoint] = await _get(GLUETUN_PORT, endpoint)
        except Exception as e:
            results[endpoint] = f"error: {e}"
    return _fmt(results)


@mcp.tool()
async def check_vpn_health() -> str:
    """Comprehensive VPN health check – verifies Gluetun is healthy, VPN IP is active, and that SABnzbd and qBittorrent are reachable through the VPN tunnel."""
    health = {"gluetun": {}, "sabnzbd": {}, "qbittorrent": {}, "overall": "healthy"}

    # Check Gluetun API and VPN IP
    try:
        ip_data = await _get(GLUETUN_PORT, "/v1/publicip/ip")
        health["gluetun"]["vpn_ip"] = ip_data
        health["gluetun"]["status"] = "connected"
    except Exception as e:
        health["gluetun"]["status"] = "unreachable"
        health["gluetun"]["error"] = str(e)
        health["overall"] = "unhealthy"

    try:
        status_data = await _get(GLUETUN_PORT, "/v1/openvpn/status")
        # Note: /v1/openvpn/status reports "stopped" when using WireGuard – this is
        # expected and not an error. The VPN IP check above is the reliable indicator.
        health["gluetun"]["tunnel_status"] = status_data
        if isinstance(status_data, dict) and status_data.get("status") == "stopped":
            health["gluetun"]["tunnel_note"] = "Reports 'stopped' because WireGuard is in use (not OpenVPN) – this is normal"
    except Exception:
        pass

    # Check SABnzbd reachability (routed through Gluetun)
    try:
        data = await _get(SABNZBD_PORT, "/api", params={
            "apikey": SABNZBD_API_KEY, "output": "json", "mode": "version"
        })
        health["sabnzbd"]["status"] = "reachable"
        health["sabnzbd"]["version"] = data
    except Exception as e:
        health["sabnzbd"]["status"] = "unreachable"
        health["sabnzbd"]["error"] = str(e)
        health["overall"] = "unhealthy"

    # Check qBittorrent reachability (routed through Gluetun)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
                data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
            )
            if resp.status_code == 200:
                health["qbittorrent"]["status"] = "reachable"
            else:
                health["qbittorrent"]["status"] = "auth_failed"
                health["overall"] = "degraded"
    except Exception as e:
        health["qbittorrent"]["status"] = "unreachable"
        health["qbittorrent"]["error"] = str(e)
        health["overall"] = "unhealthy"

    # Summary
    if health["overall"] == "unhealthy":
        health["recommendation"] = "Gluetun or dependent services are down. Try: docker-compose restart gluetun && docker restart qbittorrent sabnzbd"
    elif health["overall"] == "degraded":
        health["recommendation"] = "Some services have issues. Check individual service errors above."

    return _fmt(health)


# ---------------------------------------------------------------------------
# Tools – Sonarr
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_sonarr_status() -> str:
    """Get Sonarr system status – version, health checks, disk space."""
    status = await _arr_get("sonarr", "/system/status")
    health = await _arr_get("sonarr", "/health")
    diskspace = await _arr_get("sonarr", "/diskspace")
    return _fmt({"status": status, "health": health, "diskspace": diskspace})


@mcp.tool()
async def get_sonarr_queue() -> str:
    """Get Sonarr download queue – currently downloading/importing episodes."""
    data = await _arr_get("sonarr", "/queue?pageSize=50&includeUnknownSeriesItems=true&includeSeries=true&includeEpisode=true")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for item in records:
        ep = item.get("episode") or {}
        items.append({
            "queueId": item.get("id"),
            "series": (item.get("series") or {}).get("title") or item.get("title"),
            "episode": ep.get("title"),
            "seasonEpisode": _se(ep.get("seasonNumber"), ep.get("episodeNumber")) if ep else None,
            "status": item.get("status"),
            "trackedDownloadStatus": item.get("trackedDownloadStatus"),
            "size": _human_bytes(item.get("size", 0)),
            "sizeleft": _human_bytes(item.get("sizeleft", 0)),
            "timeleft": item.get("timeleft"),
            "downloadClient": item.get("downloadClient"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_sonarr_calendar(days: int = 7) -> str:
    """Get upcoming episodes from Sonarr for the next N days (default 7)."""
    from datetime import datetime, timedelta
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data = await _arr_get("sonarr", f"/calendar?start={start}&end={end}&includeSeries=true")
    episodes = []
    for ep in (data if isinstance(data, list) else []):
        episodes.append({
            "series": (ep.get("series") or {}).get("title"),
            "seasonEpisode": _se(ep.get("seasonNumber"), ep.get("episodeNumber")),
            "title": ep.get("title"),
            "airDate": ep.get("airDate"),
            "hasFile": ep.get("hasFile"),
            "overview": ep.get("overview"),
        })
    return _fmt(episodes)


@mcp.tool()
async def get_sonarr_activity(page: int = 1, page_size: int = 20) -> str:
    """Get Sonarr recent activity/history."""
    data = await _arr_get("sonarr", f"/history?page={page}&pageSize={page_size}&sortKey=date&sortDirection=descending&includeSeries=true&includeEpisode=true")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        ep = r.get("episode") or {}
        items.append({
            "eventType": r.get("eventType"),
            "series": (r.get("series") or {}).get("title"),
            "seasonEpisode": _se(ep.get("seasonNumber"), ep.get("episodeNumber")) if ep else None,
            "episodeTitle": ep.get("title"),
            "sourceTitle": r.get("sourceTitle"),
            "date": r.get("date"),
            "quality": (r.get("quality") or {}).get("quality", {}).get("name"),
            "downloadClient": (r.get("data") or {}).get("downloadClientName"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_sonarr_missing(page: int = 1, page_size: int = 20) -> str:
    """Get Sonarr wanted/missing episodes – monitored episodes that haven't been downloaded yet."""
    data = await _arr_get("sonarr", f"/wanted/missing?page={page}&pageSize={page_size}&sortKey=airDateUtc&sortDirection=descending&includeSeries=true")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        items.append({
            "seriesId": r.get("seriesId"),
            "series": (r.get("series") or {}).get("title"),
            "seasonEpisode": _se(r.get("seasonNumber"), r.get("episodeNumber")),
            "title": r.get("title"),
            "airDate": r.get("airDate"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def search_sonarr_series(term: str) -> str:
    """Search for a TV series in your Sonarr library by name. Returns matching series with stats."""
    all_series = await _arr_get("sonarr", "/series")
    term_lower = term.lower()
    matches = []
    for s in (all_series if isinstance(all_series, list) else []):
        if term_lower in s.get("title", "").lower() or term_lower in s.get("sortTitle", "").lower():
            stats = s.get("statistics") or {}
            matches.append({
                "id": s.get("id"),
                "title": s.get("title"),
                "year": s.get("year"),
                "status": s.get("status"),
                "seasonCount": stats.get("seasonCount"),
                "episodeCount": stats.get("episodeCount"),
                "episodeFileCount": stats.get("episodeFileCount"),
                "sizeOnDisk": _human_bytes(stats.get("sizeOnDisk", 0)),
                "percentOfEpisodes": stats.get("percentOfEpisodes"),
                "monitored": s.get("monitored"),
                "network": s.get("network"),
            })
    return _fmt({"matches": len(matches), "series": matches})


@mcp.tool()
async def get_sonarr_library_stats() -> str:
    """Get Sonarr library statistics – total series, episodes, file counts, and disk usage."""
    all_series = await _arr_get("sonarr", "/series")
    if not isinstance(all_series, list):
        return _fmt({"error": "Could not fetch series list"})
    total_series = len(all_series)
    total_episodes = 0
    total_episode_files = 0
    total_size = 0
    monitored = 0
    continuing = 0
    for s in all_series:
        stats = s.get("statistics") or {}
        total_episodes += stats.get("episodeCount", 0)
        total_episode_files += stats.get("episodeFileCount", 0)
        total_size += stats.get("sizeOnDisk", 0)
        if s.get("monitored"):
            monitored += 1
        if s.get("status") == "continuing":
            continuing += 1
    return _fmt({
        "totalSeries": total_series,
        "monitored": monitored,
        "continuing": continuing,
        "ended": total_series - continuing,
        "totalEpisodes": total_episodes,
        "totalEpisodeFiles": total_episode_files,
        "missingEpisodes": total_episodes - total_episode_files,
        "totalSizeOnDisk": _human_bytes(total_size),
    })


# ---------------------------------------------------------------------------
# Tools – Radarr
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_radarr_status() -> str:
    """Get Radarr system status – version, health checks, disk space."""
    status = await _arr_get("radarr", "/system/status")
    health = await _arr_get("radarr", "/health")
    diskspace = await _arr_get("radarr", "/diskspace")
    return _fmt({"status": status, "health": health, "diskspace": diskspace})


@mcp.tool()
async def get_radarr_queue() -> str:
    """Get Radarr download queue – currently downloading/importing movies."""
    data = await _arr_get("radarr", "/queue?pageSize=50&includeUnknownMovieItems=true&includeMovie=true")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for item in records:
        movie = item.get("movie") or {}
        items.append({
            "queueId": item.get("id"),
            "title": movie.get("title") or item.get("title"),
            "year": movie.get("year"),
            "status": item.get("status"),
            "trackedDownloadStatus": item.get("trackedDownloadStatus"),
            "size": _human_bytes(item.get("size", 0)),
            "sizeleft": _human_bytes(item.get("sizeleft", 0)),
            "timeleft": item.get("timeleft"),
            "downloadClient": item.get("downloadClient"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_radarr_calendar(days: int = 30) -> str:
    """Get upcoming movies from Radarr for the next N days (default 30)."""
    from datetime import datetime, timedelta
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data = await _arr_get("radarr", f"/calendar?start={start}&end={end}")
    movies = []
    for m in (data if isinstance(data, list) else []):
        movies.append({
            "title": m.get("title"),
            "year": m.get("year"),
            "releaseDate": m.get("physicalRelease") or m.get("digitalRelease"),
            "inCinemas": m.get("inCinemas"),
            "hasFile": m.get("hasFile"),
            "status": m.get("status"),
        })
    return _fmt(movies)


@mcp.tool()
async def get_radarr_activity(page: int = 1, page_size: int = 20) -> str:
    """Get Radarr recent activity/history."""
    data = await _arr_get("radarr", f"/history?page={page}&pageSize={page_size}&sortKey=date&sortDirection=descending&includeMovie=true")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        movie = r.get("movie") or {}
        items.append({
            "eventType": r.get("eventType"),
            "movie": movie.get("title"),
            "year": movie.get("year"),
            "sourceTitle": r.get("sourceTitle"),
            "date": r.get("date"),
            "quality": (r.get("quality") or {}).get("quality", {}).get("name"),
            "downloadClient": (r.get("data") or {}).get("downloadClientName"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_radarr_missing(page: int = 1, page_size: int = 20) -> str:
    """Get Radarr wanted/missing movies – monitored movies not yet downloaded."""
    data = await _arr_get("radarr", f"/wanted/missing?page={page}&pageSize={page_size}&sortKey=digitalRelease&sortDirection=descending")
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        items.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "year": r.get("year"),
            "status": r.get("status"),
            "digitalRelease": r.get("digitalRelease"),
            "physicalRelease": r.get("physicalRelease"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def search_radarr_movies(term: str) -> str:
    """Search for a movie in your Radarr library by name. Returns matching movies with details."""
    all_movies = await _arr_get("radarr", "/movie")
    term_lower = term.lower()
    matches = []
    for m in (all_movies if isinstance(all_movies, list) else []):
        if term_lower in m.get("title", "").lower() or term_lower in m.get("sortTitle", "").lower() or term_lower in m.get("originalTitle", "").lower():
            mf = m.get("movieFile") or {}
            matches.append({
                "id": m.get("id"),
                "title": m.get("title"),
                "year": m.get("year"),
                "status": m.get("status"),
                "hasFile": m.get("hasFile"),
                "monitored": m.get("monitored"),
                "sizeOnDisk": _human_bytes(m.get("sizeOnDisk", 0)),
                "quality": (mf.get("quality") or {}).get("quality", {}).get("name") if mf else None,
                "runtime": m.get("runtime"),
                "genres": m.get("genres", [])[:3],
            })
    return _fmt({"matches": len(matches), "movies": matches})


@mcp.tool()
async def get_radarr_library_stats() -> str:
    """Get Radarr library statistics – total movies, file counts, and disk usage."""
    all_movies = await _arr_get("radarr", "/movie")
    if not isinstance(all_movies, list):
        return _fmt({"error": "Could not fetch movie list"})
    total = len(all_movies)
    with_file = sum(1 for m in all_movies if m.get("hasFile"))
    monitored = sum(1 for m in all_movies if m.get("monitored"))
    total_size = sum(m.get("sizeOnDisk", 0) for m in all_movies)
    return _fmt({
        "totalMovies": total,
        "withFile": with_file,
        "missing": total - with_file,
        "monitored": monitored,
        "totalSizeOnDisk": _human_bytes(total_size),
    })


# ---------------------------------------------------------------------------
# Tools – SABnzbd
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_sabnzbd_status() -> str:
    """Get SABnzbd status – speed, queue size, disk space, paused state."""
    data = await _get(SABNZBD_PORT, "/api", params={
        "apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue"
    })
    q = data.get("queue", {}) if isinstance(data, dict) else {}
    return _fmt({
        "status": q.get("status"),
        "speed": q.get("speed"),
        "size": q.get("size"),
        "sizeLeft": q.get("sizeleft"),
        "timeLeft": q.get("timeleft"),
        "diskspace1": q.get("diskspace1"),
        "diskspace2": q.get("diskspace2"),
        "paused": q.get("paused"),
        "noofslots": q.get("noofslots"),
        "slots": [
            {"nzo_id": s.get("nzo_id"), "filename": s.get("filename"), "size": s.get("size"),
             "sizeleft": s.get("sizeleft"), "status": s.get("status"),
             "percentage": s.get("percentage"), "timeleft": s.get("timeleft")}
            for s in q.get("slots", [])[:20]
        ],
    })


@mcp.tool()
async def get_sabnzbd_history(limit: int = 20) -> str:
    """Get SABnzbd download history."""
    data = await _get(SABNZBD_PORT, "/api", params={
        "apikey": SABNZBD_API_KEY, "output": "json", "mode": "history", "limit": str(limit)
    })
    h = data.get("history", {}) if isinstance(data, dict) else {}
    slots = []
    for s in h.get("slots", [])[:limit]:
        slots.append({
            "nzo_id": s.get("nzo_id"),
            "name": s.get("name"),
            "size": s.get("size"),
            "status": s.get("status"),
            "completed": s.get("completed"),
            "category": s.get("category"),
        })
    return _fmt({"totalSize": h.get("total_size"), "items": slots})


# ---------------------------------------------------------------------------
# Tools – qBittorrent
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

        torrents = (await client.get(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/info"),
            params={"filter": "active", "limit": "30"},
        )).json()

        summary = []
        for t in torrents:
            summary.append({
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
            })

        return _fmt({
            "transfer": {
                "dl_info_speed": _human_bytes(info.get("dl_info_speed", 0)) + "/s",
                "up_info_speed": _human_bytes(info.get("up_info_speed", 0)) + "/s",
                "dl_info_data": _human_bytes(info.get("dl_info_data", 0)),
                "up_info_data": _human_bytes(info.get("up_info_data", 0)),
                "connection_status": info.get("connection_status"),
            },
            "active_torrents": summary,
        })


@mcp.tool()
async def get_qbittorrent_torrents(filter: str = "all", limit: int = 50) -> str:
    """List qBittorrent torrents. Filter: all, downloading, seeding, completed, paused, active, stalled."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        await client.post(
            _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
            data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
        )
        torrents = (await client.get(
            _url(QBITTORRENT_PORT, "/api/v2/torrents/info"),
            params={"filter": filter, "limit": str(limit)},
        )).json()

        summary = []
        for t in torrents:
            summary.append({
                "name": t.get("name"),
                "hash": t.get("hash"),
                "state": t.get("state"),
                "progress": f"{t.get('progress', 0) * 100:.1f}%",
                "size": _human_bytes(t.get("size", 0)),
                "ratio": f"{t.get('ratio', 0):.2f}",
                "category": t.get("category"),
                "added_on": t.get("added_on"),
            })
        return _fmt({"count": len(summary), "torrents": summary})


# ---------------------------------------------------------------------------
# Tools – Prowlarr
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tools – Readarr
# ---------------------------------------------------------------------------

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
        items.append({
            "title": item.get("title"),
            "status": item.get("status"),
            "size": _human_bytes(item.get("size", 0)),
            "sizeleft": _human_bytes(item.get("sizeleft", 0)),
            "timeleft": item.get("timeleft"),
            "downloadClient": item.get("downloadClient"),
        })
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


# ---------------------------------------------------------------------------
# Tools – Bazarr
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tools – Seerr
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_seerr_status() -> str:
    """Get Seerr status and recent media requests with titles resolved from TMDB."""
    headers = {"X-Api-Key": SEERR_API_KEY}
    status = await _get(SEERR_PORT, "/api/v1/status", headers=headers)
    requests_data = await _get(SEERR_PORT, "/api/v1/request?take=20&sort=added", headers=headers)

    items = []
    if isinstance(requests_data, dict):
        for r in requests_data.get("results", []):
            media = r.get("media") or {}
            tmdb_id = media.get("tmdbId")
            media_type = r.get("type") or media.get("mediaType")
            title = None

            # Resolve title from TMDB via Seerr
            if tmdb_id and media_type:
                try:
                    endpoint = "movie" if media_type == "movie" else "tv"
                    detail = await _get(SEERR_PORT, f"/api/v1/{endpoint}/{tmdb_id}", headers=headers)
                    title = detail.get("title") or detail.get("name") if isinstance(detail, dict) else None
                except Exception:
                    pass

            requested_by = r.get("requestedBy") or {}
            items.append({
                "id": r.get("id"),
                "title": title,
                "type": media_type,
                "status": r.get("status"),
                "mediaStatus": media.get("status"),
                "requestedBy": requested_by.get("displayName") or requested_by.get("plexUsername"),
                "createdAt": r.get("createdAt"),
            })
    return _fmt({"status": status, "recentRequests": items})


# ===========================================================================
# ACTION TOOLS – Write/Manage operations
# ===========================================================================


# ---------------------------------------------------------------------------
# Actions – Sonarr
# ---------------------------------------------------------------------------

@mcp.tool()
async def lookup_sonarr_series(term: str) -> str:
    """Search for a TV series on TVDB/TMDB to add to Sonarr. Returns results with tvdbId needed for adding."""
    data = await _arr_get("sonarr", f"/series/lookup?term={term}")
    results = []
    for s in (data if isinstance(data, list) else [])[:10]:
        results.append({
            "title": s.get("title"),
            "year": s.get("year"),
            "tvdbId": s.get("tvdbId"),
            "overview": (s.get("overview") or "")[:150],
            "seasonCount": s.get("seasonCount"),
            "network": s.get("network"),
            "status": s.get("status"),
            "alreadyInLibrary": s.get("id") is not None and s.get("id") != 0,
        })
    return _fmt(results)


@mcp.tool()
async def add_sonarr_series(tvdb_id: int, quality_profile: str = "HD - 720p/1080p", monitored: bool = True) -> str:
    """Add a new TV series to Sonarr by TVDB ID. Use lookup_sonarr_series first to find the tvdbId.
    Quality profiles: Any, SD, HD-720p, HD-1080p, Ultra-HD, HD - 720p/1080p, HD - Ultra HD."""
    # Look up the series to get full metadata
    data = await _arr_get("sonarr", f"/series/lookup?term=tvdb:{tvdb_id}")
    if not isinstance(data, list) or not data:
        return _fmt({"error": f"Series with tvdbId {tvdb_id} not found"})

    series = data[0]
    if series.get("id"):
        return _fmt({"error": f"'{series.get('title')}' is already in your library"})

    # Resolve quality profile ID
    profiles = await _arr_get("sonarr", "/qualityprofile")
    profile_id = None
    for p in (profiles if isinstance(profiles, list) else []):
        if p.get("name", "").lower() == quality_profile.lower():
            profile_id = p.get("id")
            break
    if not profile_id:
        return _fmt({"error": f"Quality profile '{quality_profile}' not found", "available": [p.get("name") for p in profiles]})

    # Get root folder
    roots = await _arr_get("sonarr", "/rootfolder")
    root_path = roots[0].get("path") if isinstance(roots, list) and roots else "/data/media/tv"

    series["qualityProfileId"] = profile_id
    series["rootFolderPath"] = root_path
    series["monitored"] = monitored
    series["addOptions"] = {"searchForMissingEpisodes": True}

    result = await _arr_post("sonarr", "/series", json_data=series)
    return _fmt({"success": True, "title": result.get("title"), "id": result.get("id"), "seasons": result.get("seasonCount")})


@mcp.tool()
async def sonarr_search_missing(series_id: int = 0) -> str:
    """Trigger a search for missing episodes. If series_id is 0, searches all missing episodes (cutoff unmet)."""
    if series_id:
        result = await _arr_post("sonarr", "/command", json_data={"name": "SeriesSearch", "seriesId": series_id})
    else:
        result = await _arr_post("sonarr", "/command", json_data={"name": "MissingEpisodeSearch"})
    return _fmt({"triggered": True, "commandId": result.get("id"), "status": result.get("status")})


@mcp.tool()
async def sonarr_remove_from_queue(queue_id: int, blocklist: bool = False) -> str:
    """Remove a stuck/failed item from the Sonarr download queue. Set blocklist=True to prevent re-downloading."""
    result = await _arr_delete("sonarr", f"/queue/{queue_id}", params={"removeFromClient": "true", "blocklist": str(blocklist).lower()})
    return _fmt({"success": True, "removed": queue_id, "blocklisted": blocklist})


# ---------------------------------------------------------------------------
# Actions – Radarr
# ---------------------------------------------------------------------------

@mcp.tool()
async def lookup_radarr_movies(term: str) -> str:
    """Search for a movie on TMDB to add to Radarr. Returns results with tmdbId needed for adding."""
    data = await _arr_get("radarr", f"/movie/lookup?term={term}")
    results = []
    for m in (data if isinstance(data, list) else [])[:10]:
        results.append({
            "title": m.get("title"),
            "year": m.get("year"),
            "tmdbId": m.get("tmdbId"),
            "overview": (m.get("overview") or "")[:150],
            "runtime": m.get("runtime"),
            "genres": m.get("genres", [])[:3],
            "status": m.get("status"),
            "alreadyInLibrary": m.get("id") is not None and m.get("id") != 0,
        })
    return _fmt(results)


@mcp.tool()
async def add_radarr_movie(tmdb_id: int, quality_profile: str = "HD - 720p/1080p", monitored: bool = True) -> str:
    """Add a new movie to Radarr by TMDB ID. Use lookup_radarr_movies first to find the tmdbId.
    Quality profiles: Any, SD, HD-720p, HD-1080p, Ultra-HD, HD - 720p/1080p."""
    data = await _arr_get("radarr", f"/movie/lookup/tmdb?tmdbId={tmdb_id}")
    if not isinstance(data, dict) or not data:
        return _fmt({"error": f"Movie with tmdbId {tmdb_id} not found"})

    movie = data
    if movie.get("id"):
        return _fmt({"error": f"'{movie.get('title')}' is already in your library"})

    profiles = await _arr_get("radarr", "/qualityprofile")
    profile_id = None
    for p in (profiles if isinstance(profiles, list) else []):
        if p.get("name", "").lower() == quality_profile.lower():
            profile_id = p.get("id")
            break
    if not profile_id:
        return _fmt({"error": f"Quality profile '{quality_profile}' not found", "available": [p.get("name") for p in profiles]})

    roots = await _arr_get("radarr", "/rootfolder")
    root_path = roots[0].get("path") if isinstance(roots, list) and roots else "/data/media/movies"

    movie["qualityProfileId"] = profile_id
    movie["rootFolderPath"] = root_path
    movie["monitored"] = monitored
    movie["addOptions"] = {"searchForMovie": True}

    result = await _arr_post("radarr", "/movie", json_data=movie)
    return _fmt({"success": True, "title": result.get("title"), "year": result.get("year"), "id": result.get("id")})


@mcp.tool()
async def radarr_search_missing(movie_id: int = 0) -> str:
    """Trigger a search for a specific movie (by movie_id) or all missing movies (movie_id=0)."""
    if movie_id:
        result = await _arr_post("radarr", "/command", json_data={"name": "MoviesSearch", "movieIds": [movie_id]})
    else:
        result = await _arr_post("radarr", "/command", json_data={"name": "MissingMoviesSearch"})
    return _fmt({"triggered": True, "commandId": result.get("id"), "status": result.get("status")})


@mcp.tool()
async def radarr_remove_from_queue(queue_id: int, blocklist: bool = False) -> str:
    """Remove a stuck/failed item from the Radarr download queue. Set blocklist=True to prevent re-downloading."""
    result = await _arr_delete("radarr", f"/queue/{queue_id}", params={"removeFromClient": "true", "blocklist": str(blocklist).lower()})
    return _fmt({"success": True, "removed": queue_id, "blocklisted": blocklist})


# ---------------------------------------------------------------------------
# Actions – SABnzbd
# ---------------------------------------------------------------------------

@mcp.tool()
async def sabnzbd_pause_resume(action: str = "pause") -> str:
    """Pause or resume the SABnzbd download queue. Action: 'pause' or 'resume'."""
    mode = "pause" if action == "pause" else "resume"
    data = await _get(SABNZBD_PORT, "/api", params={
        "apikey": SABNZBD_API_KEY, "output": "json", "mode": mode
    })
    return _fmt({"action": mode, "result": data})


@mcp.tool()
async def sabnzbd_delete_job(nzo_id: str) -> str:
    """Delete a job from SABnzbd queue by its nzo_id. Get IDs from get_sabnzbd_status."""
    data = await _get(SABNZBD_PORT, "/api", params={
        "apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue",
        "name": "delete", "value": nzo_id
    })
    return _fmt({"deleted": nzo_id, "result": data})


@mcp.tool()
async def sabnzbd_retry_failed(nzo_id: str) -> str:
    """Retry a failed SABnzbd download by its nzo_id. Get IDs from get_sabnzbd_history."""
    data = await _get(SABNZBD_PORT, "/api", params={
        "apikey": SABNZBD_API_KEY, "output": "json", "mode": "retry",
        "value": nzo_id
    })
    return _fmt({"retried": nzo_id, "result": data})


# ---------------------------------------------------------------------------
# Actions – qBittorrent
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


# ---------------------------------------------------------------------------
# Actions – Seerr
# ---------------------------------------------------------------------------

@mcp.tool()
async def seerr_approve_request(request_id: int) -> str:
    """Approve a pending Seerr media request by its ID."""
    headers = {"X-Api-Key": SEERR_API_KEY}
    result = await _post(SEERR_PORT, f"/api/v1/request/{request_id}/approve", headers=headers)
    return _fmt({"approved": request_id, "result": result})


@mcp.tool()
async def seerr_decline_request(request_id: int) -> str:
    """Decline a pending Seerr media request by its ID."""
    headers = {"X-Api-Key": SEERR_API_KEY}
    result = await _post(SEERR_PORT, f"/api/v1/request/{request_id}/decline", headers=headers)
    return _fmt({"declined": request_id, "result": result})


# ---------------------------------------------------------------------------
# Tools – Dashboard / Overview
# ---------------------------------------------------------------------------

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
        data = await _get(SABNZBD_PORT, "/api", params={
            "apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue"
        })
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
