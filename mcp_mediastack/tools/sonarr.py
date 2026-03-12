"""Sonarr tools – TV series monitoring and management."""

from datetime import datetime, timedelta

from mcp_mediastack.helpers import _arr_delete, _arr_get, _arr_post, _fmt, _human_bytes, _se
from mcp_mediastack.server import mcp

# ---------------------------------------------------------------------------
# Read tools
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
    data = await _arr_get(
        "sonarr", "/queue?pageSize=50&includeUnknownSeriesItems=true&includeSeries=true&includeEpisode=true"
    )
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for item in records:
        ep = item.get("episode") or {}
        items.append(
            {
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
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_sonarr_calendar(days: int = 7) -> str:
    """Get upcoming episodes from Sonarr for the next N days (default 7)."""
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data = await _arr_get("sonarr", f"/calendar?start={start}&end={end}&includeSeries=true")
    episodes = []
    for ep in data if isinstance(data, list) else []:
        episodes.append(
            {
                "series": (ep.get("series") or {}).get("title"),
                "seasonEpisode": _se(ep.get("seasonNumber"), ep.get("episodeNumber")),
                "title": ep.get("title"),
                "airDate": ep.get("airDate"),
                "hasFile": ep.get("hasFile"),
                "overview": ep.get("overview"),
            }
        )
    return _fmt(episodes)


@mcp.tool()
async def get_sonarr_activity(page: int = 1, page_size: int = 20) -> str:
    """Get Sonarr recent activity/history."""
    data = await _arr_get(
        "sonarr",
        f"/history?page={page}&pageSize={page_size}&sortKey=date&sortDirection=descending&includeSeries=true&includeEpisode=true",
    )
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        ep = r.get("episode") or {}
        items.append(
            {
                "eventType": r.get("eventType"),
                "series": (r.get("series") or {}).get("title"),
                "seasonEpisode": _se(ep.get("seasonNumber"), ep.get("episodeNumber")) if ep else None,
                "episodeTitle": ep.get("title"),
                "sourceTitle": r.get("sourceTitle"),
                "date": r.get("date"),
                "quality": (r.get("quality") or {}).get("quality", {}).get("name"),
                "downloadClient": (r.get("data") or {}).get("downloadClientName"),
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_sonarr_missing(page: int = 1, page_size: int = 20) -> str:
    """Get Sonarr wanted/missing episodes – monitored episodes that haven't been downloaded yet."""
    data = await _arr_get(
        "sonarr",
        f"/wanted/missing?page={page}&pageSize={page_size}&sortKey=airDateUtc&sortDirection=descending&includeSeries=true",
    )
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        items.append(
            {
                "seriesId": r.get("seriesId"),
                "series": (r.get("series") or {}).get("title"),
                "seasonEpisode": _se(r.get("seasonNumber"), r.get("episodeNumber")),
                "title": r.get("title"),
                "airDate": r.get("airDate"),
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def search_sonarr_series(term: str) -> str:
    """Search for a TV series in your Sonarr library by name. Returns matching series with stats."""
    all_series = await _arr_get("sonarr", "/series")
    term_lower = term.lower()
    matches = []
    for s in all_series if isinstance(all_series, list) else []:
        if term_lower in s.get("title", "").lower() or term_lower in s.get("sortTitle", "").lower():
            stats = s.get("statistics") or {}
            matches.append(
                {
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
                }
            )
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
    return _fmt(
        {
            "totalSeries": total_series,
            "monitored": monitored,
            "continuing": continuing,
            "ended": total_series - continuing,
            "totalEpisodes": total_episodes,
            "totalEpisodeFiles": total_episode_files,
            "missingEpisodes": total_episodes - total_episode_files,
            "totalSizeOnDisk": _human_bytes(total_size),
        }
    )


# ---------------------------------------------------------------------------
# Action tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def lookup_sonarr_series(term: str) -> str:
    """Search for a TV series on TVDB/TMDB to add to Sonarr. Returns results with tvdbId needed for adding."""
    data = await _arr_get("sonarr", f"/series/lookup?term={term}")
    results = []
    for s in (data if isinstance(data, list) else [])[:10]:
        results.append(
            {
                "title": s.get("title"),
                "year": s.get("year"),
                "tvdbId": s.get("tvdbId"),
                "overview": (s.get("overview") or "")[:150],
                "seasonCount": s.get("seasonCount"),
                "network": s.get("network"),
                "status": s.get("status"),
                "alreadyInLibrary": s.get("id") is not None and s.get("id") != 0,
            }
        )
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
    for p in profiles if isinstance(profiles, list) else []:
        if p.get("name", "").lower() == quality_profile.lower():
            profile_id = p.get("id")
            break
    if not profile_id:
        return _fmt(
            {"error": f"Quality profile '{quality_profile}' not found", "available": [p.get("name") for p in profiles]}
        )

    # Get root folder
    roots = await _arr_get("sonarr", "/rootfolder")
    root_path = roots[0].get("path") if isinstance(roots, list) and roots else "/data/media/tv"

    series["qualityProfileId"] = profile_id
    series["rootFolderPath"] = root_path
    series["monitored"] = monitored
    series["addOptions"] = {"searchForMissingEpisodes": True}

    result = await _arr_post("sonarr", "/series", json_data=series)
    return _fmt(
        {"success": True, "title": result.get("title"), "id": result.get("id"), "seasons": result.get("seasonCount")}
    )


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
    await _arr_delete(
        "sonarr", f"/queue/{queue_id}", params={"removeFromClient": "true", "blocklist": str(blocklist).lower()}
    )
    return _fmt({"success": True, "removed": queue_id, "blocklisted": blocklist})
