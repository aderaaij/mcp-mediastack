"""Overseerr / Jellyseerr tools – media request management."""

from mcp_mediastack.helpers import _fmt, _get, _post
from mcp_mediastack.server import SEERR_API_KEY, SEERR_PORT, mcp


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
            items.append(
                {
                    "id": r.get("id"),
                    "title": title,
                    "type": media_type,
                    "status": r.get("status"),
                    "mediaStatus": media.get("status"),
                    "requestedBy": requested_by.get("displayName") or requested_by.get("plexUsername"),
                    "createdAt": r.get("createdAt"),
                }
            )
    return _fmt({"status": status, "recentRequests": items})


# ---------------------------------------------------------------------------
# Action tools
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
