"""Radarr tools – movie monitoring and management."""

from datetime import datetime, timedelta

from mcp_mediastack.helpers import _arr_delete, _arr_get, _arr_post, _fmt, _human_bytes
from mcp_mediastack.server import mcp

# ---------------------------------------------------------------------------
# Read tools
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
        items.append(
            {
                "queueId": item.get("id"),
                "title": movie.get("title") or item.get("title"),
                "year": movie.get("year"),
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
async def get_radarr_calendar(days: int = 30) -> str:
    """Get upcoming movies from Radarr for the next N days (default 30)."""
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data = await _arr_get("radarr", f"/calendar?start={start}&end={end}")
    movies = []
    for m in data if isinstance(data, list) else []:
        movies.append(
            {
                "title": m.get("title"),
                "year": m.get("year"),
                "releaseDate": m.get("physicalRelease") or m.get("digitalRelease"),
                "inCinemas": m.get("inCinemas"),
                "hasFile": m.get("hasFile"),
                "status": m.get("status"),
            }
        )
    return _fmt(movies)


@mcp.tool()
async def get_radarr_activity(page: int = 1, page_size: int = 20) -> str:
    """Get Radarr recent activity/history."""
    data = await _arr_get(
        "radarr", f"/history?page={page}&pageSize={page_size}&sortKey=date&sortDirection=descending&includeMovie=true"
    )
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        movie = r.get("movie") or {}
        items.append(
            {
                "eventType": r.get("eventType"),
                "movie": movie.get("title"),
                "year": movie.get("year"),
                "sourceTitle": r.get("sourceTitle"),
                "date": r.get("date"),
                "quality": (r.get("quality") or {}).get("quality", {}).get("name"),
                "downloadClient": (r.get("data") or {}).get("downloadClientName"),
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def get_radarr_missing(page: int = 1, page_size: int = 20) -> str:
    """Get Radarr wanted/missing movies – monitored movies not yet downloaded."""
    data = await _arr_get(
        "radarr", f"/wanted/missing?page={page}&pageSize={page_size}&sortKey=digitalRelease&sortDirection=descending"
    )
    records = data.get("records", []) if isinstance(data, dict) else []
    items = []
    for r in records:
        items.append(
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "year": r.get("year"),
                "status": r.get("status"),
                "digitalRelease": r.get("digitalRelease"),
                "physicalRelease": r.get("physicalRelease"),
            }
        )
    return _fmt({"totalRecords": data.get("totalRecords", 0), "items": items})


@mcp.tool()
async def search_radarr_movies(term: str) -> str:
    """Search for a movie in your Radarr library by name. Returns matching movies with details."""
    all_movies = await _arr_get("radarr", "/movie")
    term_lower = term.lower()
    matches = []
    for m in all_movies if isinstance(all_movies, list) else []:
        if (
            term_lower in m.get("title", "").lower()
            or term_lower in m.get("sortTitle", "").lower()
            or term_lower in m.get("originalTitle", "").lower()
        ):
            mf = m.get("movieFile") or {}
            matches.append(
                {
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
                }
            )
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
    return _fmt(
        {
            "totalMovies": total,
            "withFile": with_file,
            "missing": total - with_file,
            "monitored": monitored,
            "totalSizeOnDisk": _human_bytes(total_size),
        }
    )


# ---------------------------------------------------------------------------
# Action tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def lookup_radarr_movies(term: str) -> str:
    """Search for a movie on TMDB to add to Radarr. Returns results with tmdbId needed for adding."""
    data = await _arr_get("radarr", f"/movie/lookup?term={term}")
    results = []
    for m in (data if isinstance(data, list) else [])[:10]:
        results.append(
            {
                "title": m.get("title"),
                "year": m.get("year"),
                "tmdbId": m.get("tmdbId"),
                "overview": (m.get("overview") or "")[:150],
                "runtime": m.get("runtime"),
                "genres": m.get("genres", [])[:3],
                "status": m.get("status"),
                "alreadyInLibrary": m.get("id") is not None and m.get("id") != 0,
            }
        )
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
    for p in profiles if isinstance(profiles, list) else []:
        if p.get("name", "").lower() == quality_profile.lower():
            profile_id = p.get("id")
            break
    if not profile_id:
        return _fmt(
            {"error": f"Quality profile '{quality_profile}' not found", "available": [p.get("name") for p in profiles]}
        )

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
    await _arr_delete(
        "radarr", f"/queue/{queue_id}", params={"removeFromClient": "true", "blocklist": str(blocklist).lower()}
    )
    return _fmt({"success": True, "removed": queue_id, "blocklisted": blocklist})
